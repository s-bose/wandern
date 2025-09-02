from datetime import datetime
from typing import Any

try:
    import psycopg
    from psycopg.connection import Connection
    from psycopg.rows import DictRow, dict_row
    from psycopg.sql import SQL, Identifier
except ModuleNotFoundError as exc:
    raise ImportError(
        "psycopg is required for PostgreSQL support. "
        'Install it with: pip install "wandern[postgresql]"'
    ) from exc

from wandern.databases.base import BaseProvider
from wandern.exceptions import ConnectError
from wandern.models import Config, Revision


class PostgresProvider(BaseProvider):
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
            raise ConnectError(
                "Failed to connect to the database"
                f"\nIs your database server running on '{self.config.dsn}'?"
            ) from exc

    def create_table_migration(self):
        query = SQL(
            """
            CREATE TABLE IF NOT EXISTS public.{table} (
                revision_id TEXT PRIMARY KEY NOT NULL,
                down_revision_id TEXT,
                message VARCHAR(255),
                tags TEXT[] DEFAULT NULL,
                author VARCHAR(255) DEFAULT NULL,
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

    def get_head_revision(self) -> Revision | None:
        query = SQL(
            """
            SELECT * FROM public.{table}
                ORDER BY created_at DESC LIMIT 1
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            result = connection.execute(query)
            row = result.fetchone()
            if not row:
                return None
            return Revision(**row)

    def migrate_up(self, revision: Revision):
        query = SQL(
            """
            INSERT INTO public.{table}
                VALUES (
                    %(revision_id)s,
                    %(down_revision_id)s,
                    %(message)s,
                    %(tags)s,
                    %(author)s,
                    %(created_at)s
                )
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            with connection.transaction():  # Begin transaction
                if revision.up_sql:
                    connection.execute(revision.up_sql)  # type: ignore

                result = connection.execute(
                    query,
                    params={
                        "revision_id": revision.revision_id,
                        "down_revision_id": revision.down_revision_id,
                        "message": revision.message,
                        "tags": revision.tags,
                        "author": revision.author,
                        "created_at": datetime.now(),
                    },
                )

                return result.rowcount

    def migrate_down(self, revision: Revision) -> int:
        query = SQL(
            """
            DELETE FROM public.{table}
                WHERE revision_id = %(revision_id)s
            """
        ).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            with connection.transaction():  # BEGIN
                if revision.down_sql:
                    connection.execute(revision.down_sql)  # type: ignore

                result = connection.execute(
                    query,
                    params={"revision_id": revision.revision_id},
                )

                return result.rowcount

    def list_migrations(
        self,
        author: str | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> list[Revision]:
        base_query = """
            SELECT * FROM public.{table}
        """

        where_clause = []

        params: dict[str, Any] = {}
        if author:
            where_clause.append("author = %(author)s")
            params["author"] = author
        if tags:
            where_clause.append("tags && %(tags)s")
            params["tags"] = tags
        if created_at:
            where_clause.append("created_at >= %(created_at)s")
            params["created_at"] = created_at

        if where_clause:
            base_query += f" WHERE {' AND '.join(where_clause)}"
        base_query += " ORDER BY created_at DESC"

        query = SQL(base_query).format(table=Identifier(self.config.migration_table))

        with self.connect() as connection:
            result = connection.execute(query, params=params)
            rows = result.fetchall()

            return [Revision(**row) for row in rows]
