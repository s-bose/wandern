import pytest

from wandern.databases.postgresql import PostgresProvider
from wandern.databases.provider import get_database_impl
from wandern.databases.sqlite import SQLiteProvider
from wandern.models import Config, DatabaseProviders


def test_get_database_impl_postgresql():
    """Test get_database_impl returns PostgresProvider for postgresql."""
    config = Config(
        dsn="postgresql://user:pass@localhost/test", migration_dir="./migrations"
    )

    # Test with enum
    provider = get_database_impl(DatabaseProviders.POSTGRESQL, config)
    assert isinstance(provider, PostgresProvider)

    # Test with string
    provider = get_database_impl("postgresql", config)
    assert isinstance(provider, PostgresProvider)


def test_get_database_impl_sqlite():
    """Test get_database_impl returns SQLiteProvider for sqlite."""
    config = Config(dsn="sqlite:///test.db", migration_dir="./migrations")

    # Test with enum
    provider = get_database_impl(DatabaseProviders.SQLITE, config)
    assert isinstance(provider, SQLiteProvider)

    # Test with string
    provider = get_database_impl("sqlite", config)
    assert isinstance(provider, SQLiteProvider)


def test_get_database_impl_unsupported():
    """Test get_database_impl raises NotImplementedError for unsupported providers."""
    config = Config(
        dsn="mysql://user:pass@localhost/test", migration_dir="./migrations"
    )

    # Test with enum
    with pytest.raises(
        NotImplementedError, match="Provider mysql is not implemented yet!"
    ):
        get_database_impl(DatabaseProviders.MYSQL, config)

    # Test with string
    with pytest.raises(
        NotImplementedError, match="Provider mysql is not implemented yet!"
    ):
        get_database_impl("mysql", config)


def test_get_database_impl_provider_type_conversion():
    """Test that string providers are correctly converted to DatabaseProviders enum."""
    config = Config(
        dsn="postgresql://user:pass@localhost/test", migration_dir="./migrations"
    )

    # Test that both string and enum inputs work the same way
    provider_from_string = get_database_impl("postgresql", config)
    provider_from_enum = get_database_impl(DatabaseProviders.POSTGRESQL, config)

    assert type(provider_from_string) is type(provider_from_enum)
    assert isinstance(provider_from_string, PostgresProvider)
    assert isinstance(provider_from_enum, PostgresProvider)


def test_get_database_impl_config_passed_correctly():
    """Test that the config is passed correctly to the provider."""
    config = Config(
        dsn="sqlite:///test.db",
        migration_dir="./test_migrations",
        migration_table="custom_migrations",
    )

    provider = get_database_impl(DatabaseProviders.SQLITE, config)
    assert provider.config == config
    assert provider.config.migration_table == "custom_migrations"
