from datetime import datetime
import psycopg
from psycopg.sql import SQL, Identifier
from psycopg.rows import dict_row, DictRow
from psycopg.connection import Connection
from wandern.config import Config
from wandern.exceptions import ConnectError
from wandern.databases.base import DatabaseMigration
from wandern.types import Revision


class PostgresMigration(DatabaseMigration):
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

    def migrate_up(self, revision: Revision):
        with self.connect() as connection:
            with connection.transaction():  # BEGIN
                connection.execute(revision["up_sql"])

                update_migration_sql = self.compose_update_migration_sql()
                connection.execute(
                    update_migration_sql,
                    params={
                        "revision_id": revision["revision_id"],
                        "down_revision_id": revision["down_revision_id"],
                        "timestamp": datetime.now(),
                    },
                )

    def migrate_down(self, revision: Revision) -> None:
        with self.connect() as connection:
            with connection.transaction():  # BEGIN
                connection.execute(revision["down_sql"])

                update_migration_sql = self.compose_update_migration_sql()
                connection.execute(
                    update_migration_sql,
                    params={
                        "revision_id": revision["revision_id"],
                        "down_revision_id": revision["down_revision_id"],
                        "timestamp": datetime.now(),
                    },
                )

    def compose_update_migration_sql(self):
        return SQL(
            """UPDATE public.{table}
            SET id = %(revision_id)s, down_revision = %(down_revision_id)s, created_at = %(timestamp)s
            """
        ).format(table=Identifier(self.config.migration_table))
