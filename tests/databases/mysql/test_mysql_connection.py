import mysql.connector
import pytest

from wandern.databases.mysql import MySQLProvider
from wandern.exceptions import ConnectError


def test_connect(config):
    """Test connecting to MySQL."""
    provider = MySQLProvider(config)
    connection = provider.connect()

    assert connection is not None
    assert connection.is_connected()

    connection.close()


def test_connect_invalid_dsn(config):
    """Test connecting with invalid DSN raises ConnectError."""
    config.dsn = "mysql://invalid:pass@nonexistent:3306/testdb"
    provider = MySQLProvider(config)

    with pytest.raises(ConnectError):
        provider.connect()


def test_create_table_migration(config):
    """Test creating migration table."""
    provider = MySQLProvider(config)
    provider.create_table_migration()

    with provider.connect() as connection:
        cursor = connection.cursor()
        # Check if table exists
        cursor.execute(
            f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            AND table_name = '{config.migration_table}'
            """
        )
        result = cursor.fetchone()
        assert result[0] == 1

    # Cleanup
    provider.drop_table_migration()


def test_drop_table_migration(config):
    """Test dropping migration table."""
    provider = MySQLProvider(config)

    # First create the table
    provider.create_table_migration()

    # Then drop it
    provider.drop_table_migration()

    with provider.connect() as connection:
        cursor = connection.cursor()
        # Check if table no longer exists
        cursor.execute(
            f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            AND table_name = '{config.migration_table}'
            """
        )
        result = cursor.fetchone()
        assert result[0] == 0
