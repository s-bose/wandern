from datetime import datetime
import psycopg
from psycopg.sql import SQL, Identifier
from psycopg.rows import dict_row, DictRow
from psycopg.connection import Connection
from wandern.models import Config
from wandern.exceptions import ConnectError
from wandern.databases.base import DatabaseMigration
from wandern.models import Revision


class PostgresMigration(DatabaseMigration):
    def __init__(self, config: Config):
        self.config = config

    def connect(self) -> Connection[DictRow]:
        try:
            return psycopg.connect(
                self.config.dsn,
                autocommit=True,
                row_factory=dict_row,  # type: ignore
            )
        except Exception as exc:
            raise ConnectError("Failed to connect to the database") from exc

    def create_table_migration(self):
        query = SQL(
            """
            CREATE TABLE IF NOT EXISTS public.{table} (
                revision_id TEXT PRIMARY KEY NOT NULL,
                down_revision_id TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            connection.execute(query)

    def drop_table_migration(self):
        query = SQL("""DROP TABLE IF EXISTS public.{table}""").format(
            table=Identifier(self.config.migration_table)
        )

        with self.connect() as connection:
            connection.execute(query)

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
        query = SQL(
            """
            INSERT INTO public.{table}
                VALUES (%(revision_id)s, %(down_revision_id)s, %(timestamp)s)
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            with connection.transaction():  # Begin transaction
                connection.execute(revision.up_sql or "")

                connection.execute(
                    query,
                    params={
                        "revision_id": revision.revision_id,
                        "down_revision_id": revision.down_revision_id,
                        "timestamp": datetime.now(),
                    },
                )

    def migrate_down(self, revision: Revision) -> None:
        query = SQL(
            """
            DELETE FROM public.{table}
                WHERE revision_id = %(revision_id)s
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            with connection.transaction():  # BEGIN
                connection.execute(revision.down_sql or "")

                connection.execute(
                    query,
                    params={"revision_id": revision.revision_id},
                )

    def list_migrations(self):
        query = SQL(
            """
            SELECT * FROM public.{table}
            ORDER BY created_at DESC
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            result = connection.execute(query)
            return result.fetchall()
