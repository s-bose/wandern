from typing import Protocol, Any, LiteralString

import psycopg
from psycopg.sql import SQL, Identifier
from psycopg.rows import dict_row

from wandern.config import Config


class ConnectError(Exception):
    ...

class PostgresMigrationService:
    def __init__(self, config: Config):
        self.config = config

    def connect(self):
        try:
            return psycopg.connect(self.config.dsn, autocommit=False)
        except Exception as exc:
            print("Failed to connect to the database:", exc)
            raise exc
            # raise ConnectError("Failed to connect to the database")

    def create_table_migration(self):
        query = SQL("""
        CREATE TABLE IF NOT EXISTS public.{table} (
            id TEXT PRIMARY KEY,
            down_revision TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """).format(table=Identifier(self.config.migration_table))


        connection = self.connect()
        cursor = connection.cursor()

        with connection.transaction():
            result = cursor.execute(query)
            connection.commit()
            return result.fetchone()

        cursor.close()
        connection.close()


    def get_head_revision(self):
        query = SQL("""
        SELECT * FROM public.{table}
        ORDER BY created_at DESC LIMIT 1
        """).format(table=Identifier(self.config.migration_table))

        connection = self.connect()
        cursor = connection.cursor(row_factory=dict_row)

        with connection.transaction():
            cursor.execute(query)
            result = cursor.fetchone()
            return result

        cursor.close()
        connection.close()
