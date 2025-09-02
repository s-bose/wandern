import os
from datetime import datetime

import rich

from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.databases.provider import get_database_impl
from wandern.exceptions import ConnectError
from wandern.graph import MigrationGraph
from wandern.models import Config, Revision
from wandern.templates.engine import generate_template
from wandern.utils import generate_migration_filename


class MigrationService:
    def __init__(self, config: Config):
        self.config = config
        if not config.dialect or not config.dsn:
            raise ConnectError("No database connection string provided")

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
            filtered_revisions = [rev for rev in revisions if rev.author == author]
        elif tags is not None and len(tags) > 0:
            filtered_revisions = [
                rev for rev in revisions if rev.tags and set(rev.tags) & set(tags)
            ]
        else:
            filtered_revisions = revisions

        # Validate that filtered revisions form a continuous chain
        if author is not None or tags:
            self._validate_sequential_path(filtered_revisions, head)
            revisions = filtered_revisions

        if not revisions:
            rich.print("[green]Nothing to upgrade, already up to date[/green]")
            return

        for revision in revisions:
            self.database.migrate_up(revision)
            rich.print(
                f"(UP) [green]{revision.down_revision_id} -> {revision.revision_id}[/green]"
            )
            count += 1
            if steps and count == steps:
                break

    def _validate_sequential_path(
        self, filtered_revisions: list[Revision], head: Revision | None
    ):
        if not filtered_revisions:
            return

        expected_down_revision_id = head.revision_id if head else None

        for i, revision in enumerate(filtered_revisions):
            if revision.down_revision_id != expected_down_revision_id:
                if i == 0:
                    raise ValueError(
                        f"Cannot apply migration '{revision.revision_id}' - it depends on "
                        f"'{revision.down_revision_id}' but current head is '{expected_down_revision_id}'"
                    )
                else:
                    raise ValueError(
                        f"Cannot apply migration '{revision.revision_id}' - missing dependency "
                        f"between '{filtered_revisions[i - 1].revision_id}' and '{revision.revision_id}'"
                    )

            expected_down_revision_id = revision.revision_id

    def downgrade(
        self,
        steps: int | None = None,
    ):
        self.database.create_table_migration()
        head = self.database.get_head_revision()
        if not head:
            # No migration to downgrade
            rich.print("[red]Nothing to downgrade[/red]")
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
                rich.print(f"(DOWN) [red]{current.revision_id} -> None[/red]")
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

    def get_combined_migrations(
        self,
        author: str | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> list[tuple[Revision, str]]:
        db_migrations = self.database.list_migrations(
            author=author, tags=tags, created_at=created_at
        )
        db_revision_ids = {rev.revision_id for rev in db_migrations}
        local_migrations = list(self.graph.iter())

        combined = list[tuple[Revision, str]]()

        for rev in db_migrations:
            combined.append((rev, "applied"))

        for rev in local_migrations:
            if rev.revision_id not in db_revision_ids:
                if author and rev.author != author:
                    continue
                if tags and not (rev.tags and set(rev.tags) & set(tags)):
                    continue
                if created_at and rev.created_at < created_at:
                    continue
                combined.append((rev, "not applied"))

        combined.sort(key=lambda x: x[0].created_at, reverse=True)

        return combined
