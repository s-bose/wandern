from wandern.config import Config
from wandern.databases.provider import get_database_impl
from wandern.databases.base import DatabaseMigration
from wandern.graph import MigrationGraph
from wandern.models import Revision


class MigrationService:
    def __init__(self, config: Config):
        self.config = config
        self.database = get_database_impl(config.dialect, config=config)
        self.graph = MigrationGraph.build(config.migration_dir)

    def upgrade(self, steps: int | None = None):
        head = self.database.get_head_revision()
        if not head:
            # first migration
            for revision in self.graph.iter():
                self.database.migrate_up(revision)
        else:
            for revision in self.graph.iter_from(head["revision_id"], steps=steps):
                self.database.migrate_up(revision)

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

        step = 0
        while current and (steps is None or step < steps):
            self.database.migrate_down(current)
            if not current.down_revision_id:
                break
            current = self.graph.get_node(current.down_revision_id)
            step += 1
