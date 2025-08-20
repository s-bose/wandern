from enum import StrEnum
from .base import DatabaseMigration

from .postgresql import PostgresMigration

from wandern.config import Config


class DatabaseProviders(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"  # FUTURE: not implemented
    MYSQL = "mysql"  # FUTURE: not implemented
    MSSQL = "mssql"  # FUTURE: not implemented


def get_database_impl(provider: DatabaseProviders | str, config: Config):
    provider = DatabaseProviders(provider)
    if provider == DatabaseProviders.POSTGRESQL:
        return PostgresMigration(config=config)
    else:
        raise NotImplementedError(f"Provider {provider!s} is not implemented yet!")
