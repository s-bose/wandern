import pytest

from wandern.databases.postgresql import PostgresProvider
from wandern.exceptions import ConnectError
from wandern.models import Config


def test_connect():
    """Test connection error handling without autofixtures."""
    config = Config(
        dsn="postgresql://foo:bar@localhost:5432/test",
        migration_dir="migrations",
    )
    migration = PostgresProvider(config)
    with pytest.raises(ConnectError):
        migration.connect()
