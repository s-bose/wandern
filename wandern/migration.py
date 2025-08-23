import rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.style import Style
import os
from uuid import uuid4
from datetime import datetime
from wandern.models import Config, Revision

from wandern.databases.provider import get_database_impl
from wandern.graph import MigrationGraph
from wandern.utils import generate_migration_filename
from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.templates.engine import generate_template


class MigrationService:
    def __init__(self, config: Config):
        self.config = config
        self.database = get_database_impl(config.dialect, config=config)
        self.graph = MigrationGraph.build(config.migration_dir)

    def upgrade(self, steps: int | None = None):
        self.database.create_table_migration()
        head = self.database.get_head_revision()
        count = 0

        if not head:
            # first migration
            for revision in self.graph.iter():
                self.database.migrate_up(revision)
                rich.print(
                    f"(UP) [green]{revision.down_revision_id} -> {revision.revision_id}[/green]"
                )
                count += 1
                if steps and count == steps:
                    break
        else:
            for revision in self.graph.iter_from(head["revision_id"]):
                self.database.migrate_up(revision)
                rich.print(
                    f"(UP) [green]{revision.down_revision_id} -> {revision.revision_id}[/green]"
                )
                count += 1
                if steps and count == steps:
                    break

    def downgrade(self, steps: int | None = None):
        head = self.database.get_head_revision()
        if not head:
            # No migration to downgrade
            return

        current = self.graph.get_node(head["revision_id"])
        if not current:
            raise ValueError(
                f"Migration file for revision {head['revision_id']} not found"
            )

        count = 0
        while current and (steps is None or count < steps):
            self.database.migrate_down(current)
            if not current.down_revision_id:
                break
            rich.print(
                f"(DOWN) [red]{current.revision_id} -> {current.down_revision_id}[/red]"
            )
            current = self.graph.get_node(current.down_revision_id)
            count += 1

    def create_empty_migration(
        self,
        message: str | None,
        down_revision_id: str | None,
        author: str | None = None,
        tags: list[str] | None = None,
    ) -> Revision:
        version = uuid4().hex[:8]

        return Revision(
            revision_id=version,
            down_revision_id=down_revision_id,
            message=message or "",
            tags=tags,
            author=author,
            up_sql=None,
            down_sql=None,
        )

    def save_migration(self, revision: Revision):
        filename = generate_migration_filename(
            fmt=self.config.file_format or DEFAULT_FILE_FORMAT,
            version=revision.revision_id,
            message=revision.message,
            author=revision.author,
        )

        migration_body = generate_template(
            template_filename="migration.sql.j2", revision=revision
        )

        migration_dir_abs = os.path.abspath(self.config.migration_dir)
        with open(
            os.path.join(migration_dir_abs, filename), "w", encoding="utf-8"
        ) as file:
            file.write(migration_body)

        return filename

    def list_migrations(self):
        revisions = self.database.list_migrations()

        table = Table(title="Migrations")

        table.add_column("Revision ID", style="cyan", no_wrap=True, justify="right")
        table.add_column("Down Revision", style="magenta", justify="right")
        table.add_column("Applied At", style="green", justify="right")

        if revisions:
            table.add_row(
                f'[bright_magenta](HEAD)[/bright_magenta] {revisions[0]["revision_id"]}',
                f'{revisions[0]["down_revision_id"] or "None"}',
                f'{revisions[0]["created_at"].strftime("%Y-%m-%d %H:%M:%S")}',
            )
            for rev in revisions[1:]:
                table.add_row(
                    rev["revision_id"],
                    rev["down_revision_id"] or "None",
                    rev["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                )

        rich.print(table)

        # tree = Tree("[green] Applied Migrations")
        # if revisions:
        #     # Start with the HEAD (most recent migration - first in the list)
        #     head_revision = revisions[0]

        #     # Add the HEAD node at the root
        #     head_text = (
        #         f"[bright_magenta](HEAD)[/bright_magenta] "
        #         f'{head_revision["revision_id"]} - '
        #         f'{head_revision["created_at"]}'
        #     )
        #     current_node = tree.add(head_text)

        #     # Add each subsequent migration as a child of the previous one
        #     for rev in revisions[1:]:
        #         rev_text = f'{rev["revision_id"]} - {rev["created_at"]}'
        #         current_node = current_node.add(rev_text)

        # rich.print(tree)
