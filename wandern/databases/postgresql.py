from datetime import datetime
import psycopg
from psycopg.sql import SQL, Identifier
from psycopg.rows import dict_row, DictRow
from psycopg.connection import Connection
from wandern.config import Config
from wandern.exceptions import ConnectError
from wandern.databases.base import DatabaseMigration


class PostgresMigrationService(DatabaseMigration):
    def __init__(self, config: Config):
        self.config = config

    def connect(self) -> Connection[DictRow]:
        try:
            return psycopg.connect(
                self.config.dsn, autocommit=True, row_factory=dict_row  # type: ignore
            )
        except Exception as exc:
            raise ConnectError("Failed to connect to the database") from exc

    def create_table_migration(self):
        query = SQL(
            """
        CREATE TABLE IF NOT EXISTS public.{table} (
            id TEXT PRIMARY KEY,
            down_revision TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            result = connection.execute(query)
            return result.fetchone()

    def drop_table_migration(self):
        query = SQL(
            """
        DROP TABLE IF EXISTS public.{table}
        """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            result = connection.execute(query)
            return result.fetchone()

    def get_head_revision(self) -> DictRow | None:
        query = SQL(
            """
        SELECT * FROM public.{table}
        ORDER BY created_at DESC LIMIT 1
        """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            result = connection.execute(query)
            return result.fetchone()

    def migrate_up(self, revision: str):
        pass

    def migrate_down(self, revision: str) -> None:
        pass

    def update_migration(
        self, revision_id: str, down_revision_id: str, timestamp: datetime
    ):
        query = SQL(
            """UPDATE public.{table}
            SET id = %s, down_revision = %s, created_at = %s
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            with connection.transaction():
                result = connection.execute(
                    query, (revision_id, down_revision_id, timestamp)
                )
                return result.rowcount
