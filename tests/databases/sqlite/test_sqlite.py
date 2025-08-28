import sqlite3
from datetime import datetime
import pytest
from wandern.databases.sqlite import SQLiteMigration
from wandern.models import Revision


def test_create_table_migration(config):
    """Test that migration table is created successfully."""
    migration = SQLiteMigration(config)
    migration.create_table_migration()

    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (config.migration_table,),
        )
        result = cursor.fetchone()
        assert result is not None


def test_drop_table_migration(config):
    """Test that migration table is dropped successfully."""
    migration = SQLiteMigration(config)
    migration.create_table_migration()

    # Verify table exists
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (config.migration_table,),
        )
        result = cursor.fetchone()
        assert result is not None

    # Drop table
    migration.drop_table_migration()

    # Verify table no longer exists
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (config.migration_table,),
        )
        result = cursor.fetchone()
        assert result is None


def test_get_head_revision(config):
    """Test get_head_revision returns the latest revision."""
    migration = SQLiteMigration(config)
    migration.create_table_migration()

    # Insert test data manually
    with migration.connect() as conn:
        conn.execute(
            f"""INSERT INTO {config.migration_table}
               (revision_id, down_revision_id, message, tags, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("1", None, "Test revision", "", "test_user", datetime.now().isoformat()),
        )

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision.revision_id == "1"
    assert revision.down_revision_id is None


def test_migrate_up(config):
    """Test migrating up creates table and records revision."""
    revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        down_sql="DROP TABLE users",
    )

    migration = SQLiteMigration(config)
    migration.create_table_migration()

    migration.migrate_up(revision)

    revision_db = migration.get_head_revision()
    assert revision_db is not None
    assert revision_db.revision_id == "aaaaa"
    assert revision_db.down_revision_id is None

    # Verify table was created
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = cursor.fetchone()
        assert result is not None

        # Teardown
        conn.execute(revision.down_sql)


def test_migrate_up_multiple_revision(config):
    """Test applying multiple migrations in sequence."""
    first_revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE
        )""",
        down_sql="DROP TABLE users",
    )

    second_revision = Revision(
        revision_id="bbbbb",
        down_revision_id="aaaaa",
        message="Second Revision",
        up_sql="""CREATE TABLE organizations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        down_sql="DROP TABLE organizations",
    )

    migration = SQLiteMigration(config)
    migration.create_table_migration()

    # Apply migrations
    migration.migrate_up(first_revision)
    migration.migrate_up(second_revision)

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision.revision_id == "bbbbb"
    assert revision.down_revision_id == "aaaaa"

    # Verify both tables exist
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'organizations')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "users" in tables
        assert "organizations" in tables

        # Teardown
        conn.execute(second_revision.down_sql)
        conn.execute(first_revision.down_sql)


def test_migrate_down(config):
    """Test migrating down removes table and revision record."""
    revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        down_sql="DROP TABLE users",
    )

    migration = SQLiteMigration(config)
    migration.create_table_migration()

    # Apply then revert migration
    migration.migrate_up(revision)

    # Verify table exists
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        assert cursor.fetchone() is not None

    head = migration.get_head_revision()
    assert head is not None
    assert head.revision_id == "aaaaa"

    migration.migrate_down(revision)

    # Verify table is gone
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        assert cursor.fetchone() is None

    head = migration.get_head_revision()
    assert head is None


def test_migrate_down_multiple_revision(config):
    """Test migrating down multiple revisions in sequence."""
    first_revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE
        )""",
        down_sql="DROP TABLE users",
    )

    second_revision = Revision(
        revision_id="bbbbb",
        down_revision_id="aaaaa",
        message="Second Revision",
        up_sql="""CREATE TABLE organizations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        down_sql="DROP TABLE organizations",
    )

    migration = SQLiteMigration(config)
    migration.create_table_migration()

    # Apply migrations
    migration.migrate_up(first_revision)
    migration.migrate_up(second_revision)

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision.revision_id == "bbbbb"
    assert revision.down_revision_id == "aaaaa"

    # Verify both tables exist
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'organizations')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "users" in tables
        assert "organizations" in tables

    # Migrate down second revision
    migration.migrate_down(second_revision)

    # Check only first table exists
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'organizations')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "users" in tables
        assert "organizations" not in tables

    head = migration.get_head_revision()
    assert head is not None
    assert head.revision_id == "aaaaa"
    assert head.down_revision_id is None

    # Migrate down first revision
    migration.migrate_down(first_revision)

    # Check no tables exist
    with migration.connect() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'organizations')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "users" not in tables
        assert "organizations" not in tables

    head = migration.get_head_revision()
    assert head is None
