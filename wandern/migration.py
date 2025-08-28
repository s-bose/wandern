import os
from datetime import datetime
import rich

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

    def upgrade(
        self,
        steps: int | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
    ):
        self.database.create_table_migration()
        head = self.database.get_head_revision()
        count = 0

        if not head:
            # first migration
            revisions = list(self.graph.iter())
        else:
            revisions = list(self.graph.iter_from(head.revision_id))

        if author is not None:
            revisions = [rev for rev in revisions if rev.author == author]
        if tags is not None and len(tags) > 0:
            revisions = [
                rev for rev in revisions if rev.tags and set(rev.tags) & set(tags)
            ]

        for revision in revisions:
            self.database.migrate_up(revision)
            rich.print(
                f"(UP) [green]{revision.down_revision_id} -> {revision.revision_id}[/green]"
            )
            count += 1
            if steps and count == steps:
                break

    def downgrade(
        self,
        steps: int | None = None,
    ):
        head = self.database.get_head_revision()
        if not head:
            # No migration to downgrade
            return

        current = self.graph.get_node(head.revision_id)
        if not current:
            raise ValueError(
                f"Migration file for revision {head.revision_id} not found"
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

    def filter_migrations(
        self,
        author: str | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> list[Revision]:
        return self.database.list_migrations(
            author=author, tags=tags, created_at=created_at
        )
