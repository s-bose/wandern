import sqlite3
from datetime import datetime
from wandern.databases.base import DatabaseMigration
from wandern.models import Config
from wandern.models import Revision


class SQLiteMigration(DatabaseMigration):
    def __init__(self, config: Config):
        self.config = config

    def connect(self):
        conn = sqlite3.connect(self.config.dsn)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table_migration(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.config.migration_table} (
            revision_id TEXT PRIMARY KEY NOT NULL,
            down_revision_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        with self.connect() as connection:
            connection.execute(query)

    def drop_table_migration(self):
        query = f"""
        DROP TABLE IF EXISTS {self.config.migration_table}
        """

        with self.connect() as connection:
            connection.execute(query)

    def get_head_revision(self):
        query = f"""
        SELECT * FROM {self.config.migration_table}
        ORDER BY created_at DESC LIMIT 1
        """

        with self.connect() as connection:
            result = connection.execute(query)
            return result.fetchone()

    def migrate_up(self, revision: Revision):
        query = f"""
        INSERT INTO {self.config.migration_table}
            (revision_id, down_revision_id, created_at)
        VALUES (:revision_id, :down_revision_id, :created_at)
        """

        with self.connect() as connection:
            connection.execute(revision.up_sql or "")

            connection.execute(
                query,
                {
                    "revision_id": revision.revision_id,
                    "down_revision_id": revision.down_revision_id,
                    "created_at": datetime.now(),
                },
            )

    def migrate_down(self, revision: Revision):
        query = f"""
        DELETE FROM {self.config.migration_table}
        WHERE revision_id = :revision_id
        """

        with self.connect() as connection:
            connection.execute(revision.down_sql or "")

            connection.execute(query, {"revision_id": revision.revision_id})

    def list_migrations(self):
        query = f"""
        SELECT * FROM {self.config.migration_table}
        ORDER BY created_at ASC
        """

        with self.connect() as connection:
            result = connection.execute(query)
            return result.fetchall()
