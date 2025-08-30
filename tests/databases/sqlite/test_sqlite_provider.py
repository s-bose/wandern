from datetime import datetime

import pytest

from wandern.databases.sqlite import SQLiteProvider
from wandern.models import Revision


def test_create_table_migration(config):
    """Test that migration table is created successfully."""
    migration = SQLiteProvider(config)
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
    migration = SQLiteProvider(config)
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
    migration = SQLiteProvider(config)
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

    migration = SQLiteProvider(config)
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

    migration = SQLiteProvider(config)
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

    migration = SQLiteProvider(config)
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

    migration = SQLiteProvider(config)
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


def test_connect_error():
    """Test connection error handling."""
    from wandern.exceptions import ConnectError
    from wandern.models import Config

    # Invalid DSN should raise ConnectError
    invalid_config = Config(
        dsn="sqlite:///nonexistent/directory/invalid.db", migration_dir="./test"
    )
    migration = SQLiteProvider(invalid_config)

    with pytest.raises(ConnectError):
        migration.connect()


def test_connect_dsn_parsing(config):
    """Test DSN parsing for different formats."""
    from wandern.models import Config

    # Test DSN without sqlite:// prefix
    plain_config = Config(dsn=":memory:", migration_dir="./test")
    migration = SQLiteProvider(plain_config)
    conn = migration.connect()
    assert conn is not None
    conn.close()

    # Test DSN with sqlite:// prefix
    sqlite_config = Config(dsn="sqlite:///:memory:", migration_dir="./test")
    migration = SQLiteProvider(sqlite_config)
    conn = migration.connect()
    assert conn is not None
    conn.close()


def test_list_migrations_empty(config):
    """Test list_migrations with no migrations."""
    migration = SQLiteProvider(config)
    migration.create_table_migration()

    result = migration.list_migrations()
    assert result == []


def test_list_migrations_with_data(config):
    """Test list_migrations with various filters."""
    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # Create test revisions
    revision1 = Revision(
        revision_id="test1",
        down_revision_id=None,
        message="First test",
        author="alice",
        tags=["feature", "backend"],
        up_sql="SELECT 1",
        down_sql="SELECT 2",
    )

    revision2 = Revision(
        revision_id="test2",
        down_revision_id="test1",
        message="Second test",
        author="bob",
        tags=["bugfix"],
        up_sql="SELECT 3",
        down_sql="SELECT 4",
    )

    revision3 = Revision(
        revision_id="test3",
        down_revision_id="test2",
        message="Third test",
        author="alice",
        tags=["feature", "frontend"],
        up_sql="SELECT 5",
        down_sql="SELECT 6",
    )

    # Apply all revisions
    migration.migrate_up(revision1)
    migration.migrate_up(revision2)
    migration.migrate_up(revision3)

    # Test no filters - should return all
    all_migrations = migration.list_migrations()
    assert len(all_migrations) == 3

    # Test author filter
    alice_migrations = migration.list_migrations(author="alice")
    assert len(alice_migrations) == 2
    assert all(m.author == "alice" for m in alice_migrations)

    bob_migrations = migration.list_migrations(author="bob")
    assert len(bob_migrations) == 1
    assert bob_migrations[0].author == "bob"

    # Test tags filter - single tag
    feature_migrations = migration.list_migrations(tags=["feature"])
    assert len(feature_migrations) == 2

    backend_migrations = migration.list_migrations(tags=["backend"])
    assert len(backend_migrations) == 1

    # Test multiple tags
    feature_backend = migration.list_migrations(tags=["feature", "backend"])
    assert len(feature_backend) == 2  # Should include both feature and backend matches

    # Test created_at filter
    from datetime import datetime, timedelta

    future_time = datetime.now() + timedelta(hours=1)
    future_migrations = migration.list_migrations(created_at=future_time)
    assert len(future_migrations) == 0

    past_time = datetime.now() - timedelta(hours=1)
    past_migrations = migration.list_migrations(created_at=past_time)
    assert len(past_migrations) == 3

    # Test combined filters
    alice_feature = migration.list_migrations(author="alice", tags=["feature"])
    assert len(alice_feature) == 2
    assert all(m.author == "alice" for m in alice_feature)


def test_migrate_up_without_sql(config):
    """Test migrate_up with revision that has no up_sql."""
    revision = Revision(
        revision_id="no_sql",
        down_revision_id=None,
        message="No SQL revision",
        up_sql=None,  # No SQL to execute
        down_sql=None,
    )

    migration = SQLiteProvider(config)
    migration.create_table_migration()

    result = migration.migrate_up(revision)
    assert result == 1  # Should return rowcount from INSERT

    # Verify revision was recorded
    head = migration.get_head_revision()
    assert head is not None
    assert head.revision_id == "no_sql"


def test_migrate_down_without_sql(config):
    """Test migrate_down with revision that has no down_sql."""
    revision = Revision(
        revision_id="no_down_sql",
        down_revision_id=None,
        message="No down SQL revision",
        up_sql="SELECT 1",
        down_sql=None,  # No down SQL to execute
    )

    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # First migrate up
    migration.migrate_up(revision)

    # Then migrate down
    result = migration.migrate_down(revision)
    assert result == 1  # Should return rowcount from DELETE

    # Verify revision was removed
    head = migration.get_head_revision()
    assert head is None


def test_get_head_revision_empty_tags(config):
    """Test get_head_revision with empty/null tags."""
    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # Insert revision with empty tags
    with migration.connect() as conn:
        conn.execute(
            f"""INSERT INTO {config.migration_table}
               (revision_id, down_revision_id, message, tags, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "test1",
                None,
                "Test revision",
                None,
                "test_user",
                datetime.now().isoformat(),
            ),
        )

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision.tags == []


def test_get_head_revision_with_tags(config):
    """Test get_head_revision with tags."""
    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # Insert revision with tags
    with migration.connect() as conn:
        conn.execute(
            f"""INSERT INTO {config.migration_table}
               (revision_id, down_revision_id, message, tags, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "test1",
                None,
                "Test revision",
                "tag1,tag2",
                "test_user",
                datetime.now().isoformat(),
            ),
        )

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision.tags == ["tag1", "tag2"]


def test_get_head_revision_no_created_at(config):
    """Test get_head_revision when created_at is null."""
    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # Insert revision without created_at
    with migration.connect() as conn:
        conn.execute(
            f"""INSERT INTO {config.migration_table}
               (revision_id, down_revision_id, message, tags, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test1", None, "Test revision", "", "test_user", None),
        )

    revision = migration.get_head_revision()
    assert revision is not None
    # Should use current time as default
    assert revision.created_at is not None


def test_migrate_up_return_value(config):
    """Test that migrate_up returns correct rowcount."""
    revision = Revision(
        revision_id="test_return",
        down_revision_id=None,
        message="Test return value",
        up_sql="SELECT 1",
        down_sql="SELECT 2",
    )

    migration = SQLiteProvider(config)
    migration.create_table_migration()

    result = migration.migrate_up(revision)
    assert result == 1  # Should insert exactly one row


def test_migrate_down_return_value(config):
    """Test that migrate_down returns correct rowcount."""
    revision = Revision(
        revision_id="test_down_return",
        down_revision_id=None,
        message="Test down return value",
        up_sql="SELECT 1",
        down_sql="SELECT 2",
    )

    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # First migrate up
    migration.migrate_up(revision)

    # Then migrate down and check return value
    result = migration.migrate_down(revision)
    assert result == 1  # Should delete exactly one row


def test_list_migrations_complex_tag_search(config):
    """Test list_migrations with complex tag search patterns."""
    migration = SQLiteProvider(config)
    migration.create_table_migration()

    # Create revisions with different tag patterns
    revision1 = Revision(
        revision_id="test1",
        down_revision_id=None,
        message="Test 1",
        tags=["feature"],  # Single tag
        up_sql="SELECT 1",
    )

    revision2 = Revision(
        revision_id="test2",
        down_revision_id="test1",
        message="Test 2",
        tags=["feature", "backend"],  # Multiple tags
        up_sql="SELECT 2",
    )

    revision3 = Revision(
        revision_id="test3",
        down_revision_id="test2",
        message="Test 3",
        tags=["backend", "feature", "urgent"],  # Multiple with target in middle
        up_sql="SELECT 3",
    )

    revision4 = Revision(
        revision_id="test4",
        down_revision_id="test3",
        message="Test 4",
        tags=["backend", "urgent"],  # Target at end
        up_sql="SELECT 4",
    )

    # Apply all revisions
    migration.migrate_up(revision1)
    migration.migrate_up(revision2)
    migration.migrate_up(revision3)
    migration.migrate_up(revision4)

    # Test searching for feature tag (should match patterns: exact, prefix, suffix, middle)
    feature_migrations = migration.list_migrations(tags=["feature"])
    assert len(feature_migrations) == 3  # test1, test2, test3

    # Test searching for backend tag
    backend_migrations = migration.list_migrations(tags=["backend"])
    assert len(backend_migrations) == 3  # test2, test3, test4

    # Test searching for urgent tag
    urgent_migrations = migration.list_migrations(tags=["urgent"])
    assert len(urgent_migrations) == 2  # test3, test4
