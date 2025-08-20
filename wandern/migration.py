import rich
import os
from uuid import uuid4
from datetime import datetime
from wandern.config import Config
from wandern.databases.provider import get_database_impl
from wandern.databases.base import DatabaseMigration
from wandern.graph import MigrationGraph
from wandern.models import Revision
from wandern.utils import generate_migration_filename
from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.templates import generate_template


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

    def generate_migration(
        self,
        message: str | None,
        author: str | None = None,
        tags: list[str] | None = None,
    ):
        version = uuid4().hex[:8]
        filename = generate_migration_filename(
            fmt=self.config.file_format or DEFAULT_FILE_FORMAT,
            version=version,
            message=message,
            author=author,
        )

        last_revision_content = self.graph.get_last_migration()

        revision_id = (
            last_revision_content.revision_id if last_revision_content else None
        )

        migration_body = generate_template(
            filename="migration.sql.j2",
            kwargs={
                "timestamp": datetime.now().isoformat(),
                "version": version,
                "revises": revision_id,
                "message": message,
                "tags": tags,
                "author": author,
            },
        )

        migration_dir_abs = os.path.abspath(self.config.migration_dir)
        with open(
            os.path.join(migration_dir_abs, filename), "w", encoding="utf-8"
        ) as file:
            file.write(migration_body)

        return filename
