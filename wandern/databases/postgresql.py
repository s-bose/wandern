from typing import Protocol, Any
# import asyncpg
# from asyncpg.connection import Connection
# from asyncpg.exceptions import ConnectionFailureError

import psycopg

from wandern.config import Config


class ConnectError(Exception):
    ...

class PostgresMigrationService:
    def __init__(self, config: Config):
        self.config = config

    def connect(self):
        try:
            return  psycopg.connect(self.config.dsn)
        except Exception as exc:
            print("Failed to connect to the database:", exc)
            raise exc
            # raise ConnectError("Failed to connect to the database")


    # async def create_table_migration(self):
    #     query = f"""
    #     CREATE TABLE IF NOT EXISTS {MIGRATION_DEFAULT_TABLE_NAME} (
    #         id TEXT PRIMARY KEY,
    #         down_revision TEXT,
    #         created_at TIMESTAMP DEFAULT NOW()
    #     )
    #     """
