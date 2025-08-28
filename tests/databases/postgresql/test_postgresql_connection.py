import pytest
from wandern.databases.postgresql import PostgresMigration
from wandern.models import Config
from wandern.exceptions import ConnectError


def test_connect():
    """Test connection error handling without autofixtures."""
    config = Config(
        dsn="postgresql://foo:bar@localhost:5432/test",
        migration_dir="migrations",
    )
    migration = PostgresMigration(config)
    with pytest.raises(ConnectError):
        migration.connect()
