from wandern.databases.postgresql import PostgresMigration
from wandern.databases.sqlite import SQLiteMigration
from wandern.models import DatabaseProviders, Config


def get_database_impl(provider: DatabaseProviders | str, config: Config):
    provider = DatabaseProviders(provider)
    if provider == DatabaseProviders.POSTGRESQL:
        return PostgresMigration(config=config)
    # elif provider == DatabaseProviders.SQLITE:
    #     return SQLiteMigration(config=config)
    else:
        raise NotImplementedError(f"Provider {provider!s} is not implemented yet!")
