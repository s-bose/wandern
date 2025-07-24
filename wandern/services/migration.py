from typing import Unpack
import uuid
from pathlib import Path
import asyncpg
import os
import rich
from datetime import datetime, timezone
from asyncpg import Connection
from asyncpg.exceptions import UndefinedTableError
from wandern.config import Config, FileTemplateArgs
from wandern.constants import MIGRATION_DEFAULT_TABLE_NAME, TEMPLATE_DEFAULT_FILENAME
from wandern.utils import generate_migration_filename
from wandern.templates.manager import generate_template


class MigrationService:
    def __init__(self, config: Config):
        if not config.dsn:
            raise ValueError("Missing database connection string")

        self.config = config

    def create_migration_file(
        self,
        version: str,
        revises: str | None = None,
        message: str | None = None,
        tags: list[str] | None = None,
        author: str | None = None,
        prefix: str | None = None,
    ):
        migration_dir_path = Path(self.config.migration_dir)
        if not migration_dir_path.exists():
            raise ValueError("Migration directory does not exist or invalid")

        if not migration_dir_path.is_dir():
            raise ValueError("Migration directory is not a directory")

        if not os.access(migration_dir_path, os.W_OK):
            raise ValueError("Migration directory is not writable")

        migration_filename = generate_migration_filename(
            fmt=self.config.file_format or TEMPLATE_DEFAULT_FILENAME,
            version=version,
            message=message,
            prefix=prefix,
            author=author,
        )

        current_datetime = datetime.now(timezone.utc)

        migration_sql_body = generate_template(
            filename="migration.sql.j2",
            kwargs={
                "timestamp": current_datetime.isoformat(),
                "version": version,
                "revises": revises,
                "message": message,
                "tags": tags,
                "author": author,
            },
        )

        with open(
            migration_dir_path / migration_filename,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(migration_sql_body)

        rich.print(
            f"[green]Successfully created migration file: {migration_filename}[/green]"
        )

    async def __create_migration_table(self, conn: Connection, table_name: str) -> None:
        # make the table in db
        _query = f"""CREATE TABLE IF NOT EXISTS "public"."{table_name}" (
                id varchar PRIMARY KEY NOT NULL,
                down_revision varchar NULL
            )
        """

        await conn.execute(_query)

    async def __drop_migration_table(self, conn: Connection, table_name: str) -> None:
        _query = f"""DROP TABLE IF EXISTS "public"."{table_name}"
        """

        await conn.execute(_query)

    async def __migrate_up(self, from_id: str | None, to_id: str):
        connection = await self._get_connection()

        transaction = connection.transaction()
        await transaction.start()

        try:
            if from_id is None:
                # first migration
                _query = f"""INSERT INTO {MIGRATION_DEFAULT_TABLE_NAME}
                (id, down_revision) VALUES
                    ($1, NULL)
                """

                await connection.execute(_query, to_id)
            else:
                _query = f"""UPDATE {MIGRATION_DEFAULT_TABLE_NAME}
                    SET id = $1, down_revision = $2
                    WHERE id = $2
                """

                await connection.execute(_query, to_id, from_id)
        except Exception as exc:
            rich.print(f"[red]Failed to update migration table[/red], error: {exc}")
            await transaction.rollback()

            raise exc

        else:
            await transaction.commit()
            rich.print(
                f"[green]Successfully migrated up from version: {from_id} to version: {to_id}[/green]"
            )

    async def __migrate_down(self, from_id: str, to_id: str | None):
        connection = await self._get_connection()

        transaction = connection.transaction()
        await transaction.start()

        try:
            if to_id is None:
                _query = f"""DELETE FROM {MIGRATION_DEFAULT_TABLE_NAME}
                    WHERE id = $1
                """

                await connection.execute(_query, from_id)
            else:
                _query = f"""UPDATE {MIGRATION_DEFAULT_TABLE_NAME}
                    SET id = $1, down_revision = $2
                    WHERE id = $3
                """

                await connection.execute(_query, from_id, to_id, from_id)
        except Exception as exc:
            rich.print(f"[red]Failed to update migration table[/red], error: {exc}")
            await transaction.rollback()

            raise exc
        else:
            await transaction.commit()
            rich.print(
                f"[green]Successfully migrated down from version: {from_id} to version: {to_id}[/green]"
            )

    async def reset_migrations(self):
        # TODO
        pass

    async def _get_connection(self) -> Connection:
        return (
            await asyncpg.connect(
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                host=self.config.host,
                port=self.config.port,
                ssl=self.config.sslmode,
            )
            if self.config.dsn is None
            else await asyncpg.connect(self.config.dsn)
        )
