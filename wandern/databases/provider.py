from wandern.databases.postgresql import PostgresProvider
from wandern.databases.sqlite import SQLiteProvider
from wandern.models import Config, DatabaseProviders


def get_database_impl(provider: DatabaseProviders | str, config: Config):
    provider = DatabaseProviders(provider)
    if provider == DatabaseProviders.POSTGRESQL:
        return PostgresProvider(config=config)
    elif provider == DatabaseProviders.SQLITE:
        return SQLiteProvider(config=config)
    else:
        raise NotImplementedError(f"Provider {provider!s} is not implemented yet!")
