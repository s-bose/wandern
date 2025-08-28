from wandern.databases.sqlite import SQLiteMigration
from wandern.exceptions import ConnectError
from wandern.models import Config
import pytest
import os
import platform


def test_connect_permission_denied():
    """Test connection error when trying to create database in restricted directory."""
    # Try to create database in a directory without write permissions
    if platform.system() == "Windows":
        # On Windows, try to write to C:\Windows\System32 (typically read-only for users)
        restricted_path = "sqlite:///C:/Windows/System32/test.db"
    else:
        # On Unix-like systems, try to write to /root (typically no access for regular users)
        restricted_path = "sqlite:////root/test.db"

    config = Config(
        dsn=restricted_path,
        migration_dir="migrations",
    )
    migration = SQLiteMigration(config)

    with pytest.raises(ConnectError):
        migration.connect()


def test_connect_invalid_path():
    """Test connection error with invalid file path characters."""
    # Use invalid characters that most filesystems can't handle
    invalid_chars = ':<>"|?*' if platform.system() == "Windows" else "\x00"
    invalid_path = f"sqlite:///invalid{invalid_chars}path.db"

    config = Config(
        dsn=invalid_path,
        migration_dir="migrations",
    )
    migration = SQLiteMigration(config)

    with pytest.raises(ConnectError):
        migration.connect()


def test_connect_nonexistent_directory():
    """Test connection error when trying to create database in non-existent nested directory."""
    # SQLite can't create the directory structure, only the file
    nonexistent_path = (
        "sqlite:///some/deeply/nested/nonexistent/directory/structure/test.db"
    )

    config = Config(
        dsn=nonexistent_path,
        migration_dir="migrations",
    )
    migration = SQLiteMigration(config)

    with pytest.raises(ConnectError):
        migration.connect()
