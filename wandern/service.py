import uuid
import asyncpg
import rich
from asyncpg import Connection
from asyncpg.exceptions import UndefinedTableError
from wandern.config import Config
from wandern.constants import MIGRATION_DEFAULT_TABLE_NAME


class MigrationService:
    def __init__(self, config: Config):
        self.config = config

    def generate_revision_id(self, prev_id: str | None):
        if self.config.integer_version:
            rev_id_int = int(prev_id) + 1 if prev_id else 1

            return "{0:04d}".format(rev_id_int)

        else:
            return uuid.uuid4().hex[-12:]

    async def init_migration_table(self):
        # make the table in db
        _query = f"""CREATE TABLE IF NOT EXISTS "public"."{MIGRATION_DEFAULT_TABLE_NAME}" (
                id varchar PRIMARY KEY NOT NULL,
                down_revision varchar NULL,
            )
        """
        connection = await self._get_connection()

        async with connection.transaction():
            try:
                await connection.execute(_query)
            except Exception as exc:
                rich.print(f"[red]Failed to create migration table[/red], error: {exc}")
                raise exc

        await connection.close()

    async def update_migration_up(self, from_id: str | None, to_id: str):
        connection = await self._get_connection()

        try:
            await connection.execute(
                f"SELECT * FROM {MIGRATION_DEFAULT_TABLE_NAME} LIMIT 1"
            )
        except UndefinedTableError:
            rich.print(
                f"[red]Failed to update migration table, table {MIGRATION_DEFAULT_TABLE_NAME} does not exist[/red]"
            )

        transaction = connection.transaction()
        await transaction.start()

        try:
            if from_id is None:
                # first migration
                _query = f"""INSERT INTO {MIGRATION_DEFAULT_TABLE_NAME} (id, down_revision) VALUES
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
                f"[green]Successfully migrated from version: {from_id} to version: {to_id}[/green]"
            )

        await connection.close()

    async def update_migration_down(self, from_id: str, to_id: str | None):
        connection = await self._get_connection()

        try:
            await connection.execute(
                f"SELECT * FROM {MIGRATION_DEFAULT_TABLE_NAME} LIMIT 1"
            )
        except UndefinedTableError:
            rich.print(
                f"[red]Failed to update migration table, table {MIGRATION_DEFAULT_TABLE_NAME} does not exist[/red]"
            )

        transaction = connection.transaction()
        await transaction.start()

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

        await transaction.commit()

        await connection.close()

    async def _get_connection(self) -> Connection:
        return await asyncpg.connect(
            user=self.config.username,
            password=self.config.password,
            database=self.config.database,
            host=self.config.host,
            port=self.config.port,
            ssl=self.config.sslmode,
        )
