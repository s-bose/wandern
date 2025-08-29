from datetime import datetime
import psycopg
import pytest
from psycopg.sql import SQL, Identifier
from wandern.databases.postgresql import PostgresProvider
from wandern.models import Revision


@pytest.fixture(scope="function", autouse=True)
def truncate_table_migration(config):
    """run truncate at the end of function execution"""
    yield

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            query = SQL(
                """SELECT EXISTS (
                    SELECT FROM information_schema.tables
                        WHERE table_name = %(migration_table)s
                        AND table_schema = 'public'
                    )
                """
            )
            cur.execute(query, {"migration_table": config.migration_table})
            result = cur.fetchone()
            if result and result[0]:
                cur.execute(
                    SQL("""TRUNCATE public.{table}""").format(
                        table=Identifier(config.migration_table)
                    )
                )


def test_create_table_migration(config):
    migration = PostgresProvider(config)
    migration.create_table_migration()

    query = SQL(
        """SELECT EXISTS (
        SELECT FROM information_schema.tables
            WHERE table_name = %(migration_table)s
            AND table_schema = 'public'
        )
        """
    )
    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"migration_table": config.migration_table})
            assert cur.fetchone() is not None


def test_drop_table_migration(config):
    migration = PostgresProvider(config)
    migration.create_table_migration()

    query = SQL(
        """SELECT EXISTS (
        SELECT FROM information_schema.tables
            WHERE table_name = %(migration_table)s
            AND table_schema = 'public'
        )
        """
    )
    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"migration_table": config.migration_table})
            result = cur.fetchone()

            assert result
            assert result[0] is True

            migration.drop_table_migration()
            cur.execute(query, {"migration_table": config.migration_table})
            result = cur.fetchone()

            assert result
            assert result[0] is False


def test_get_head_revision(config):
    migration = PostgresProvider(config)
    migration.create_table_migration()

    query = SQL(
        """
        INSERT INTO public.{table}
        VALUES ( %(revision_id)s, %(down_revision_id)s, %(message)s, %(tags)s, %(author)s, %(created_at)s )
        """
    ).format(table=Identifier(config.migration_table))

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                {
                    "revision_id": "1",
                    "down_revision_id": None,
                    "message": "Test revision",
                    "tags": [],
                    "author": "test_user",
                    "created_at": datetime.now(),
                },
            )

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision.revision_id == "1"
    assert revision.down_revision_id is None


def test_migrate_up(config):
    revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="DROP TABLE public.users",
    )

    migration = PostgresProvider(config)
    migration.create_table_migration()

    migration.migrate_up(revision)

    revision_db = migration.get_head_revision()
    assert revision_db is not None

    assert revision_db.revision_id == "aaaaa"
    assert revision_db.down_revision_id is None

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                SQL(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public')"
                )
            )
            result = cur.fetchone()
            assert result
            assert result[0] is True

            # Teardown
            if revision.down_sql:
                cur.execute(revision.down_sql)


def test_migrate_up_multiple_revision(config):
    first_revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="DROP TABLE public.users",
    )

    second_revision = Revision(
        revision_id="bbbbb",
        down_revision_id="aaaaa",
        message="Second Revision",
        up_sql="""CREATE TABLE IF NOT EXISTS public.organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="""DROP TABLE public.organizations
        """,
    )
    # Setup
    migration = PostgresProvider(config)
    migration.create_table_migration()

    # Apply migrations
    migration.migrate_up(first_revision)
    migration.migrate_up(second_revision)

    revision = migration.get_head_revision()
    assert revision
    assert revision.revision_id == "bbbbb"
    assert revision.down_revision_id == "aaaaa"

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                SQL(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            result = cur.fetchall()
            assert result
            assert ("users",) in result
            assert ("organizations",) in result

            if second_revision.down_sql:
                cur.execute(second_revision.down_sql)
            if first_revision.down_sql:
                cur.execute(first_revision.down_sql)


def test_migrate_down(config):
    revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="DROP TABLE public.users",
    )

    migration = PostgresProvider(config)
    migration.create_table_migration()

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            migration.migrate_up(revision)

            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            result = cur.fetchall()
            assert result
            assert ("users",) in result

            head = migration.get_head_revision()
            assert head
            assert head.revision_id == "aaaaa"

            migration.migrate_down(revision)

            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            result = cur.fetchall()
            assert result
            assert ("users",) not in result

            head = migration.get_head_revision()
            assert head is None


def test_migrate_down_multiple_revision(config):
    first_revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="DROP TABLE public.users",
    )

    second_revision = Revision(
        revision_id="bbbbb",
        down_revision_id="aaaaa",
        message="Second Revision",
        up_sql="""CREATE TABLE IF NOT EXISTS public.organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="""DROP TABLE public.organizations
        """,
    )

    # Setup
    migration = PostgresProvider(config)
    migration.create_table_migration()

    # Apply migrations
    migration.migrate_up(first_revision)
    migration.migrate_up(second_revision)

    revision = migration.get_head_revision()
    assert revision
    assert revision.revision_id == "bbbbb"
    assert revision.down_revision_id == "aaaaa"

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            result = cur.fetchall()
            assert result
            assert ("users",) in result
            assert ("organizations",) in result

            migration.migrate_down(second_revision)

            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            result = cur.fetchall()
            assert result
            assert ("users",) in result
            assert ("organizations",) not in result

            head = migration.get_head_revision()
            assert head
            assert head.revision_id == "aaaaa"
            assert head.down_revision_id is None

            migration.migrate_down(first_revision)

            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            result = cur.fetchall()
            assert result
            assert ("users",) not in result
            assert ("organizations",) not in result

            head = migration.get_head_revision()
            assert head is None


def test_connect_error():
    """Test connection error handling."""
    from wandern.models import Config
    from wandern.exceptions import ConnectError

    # Invalid DSN should raise ConnectError
    invalid_config = Config(
        dsn="postgresql://invalid:invalid@nonexistent:99999/invalid",
        migration_dir="./test",
    )
    migration = PostgresProvider(invalid_config)

    with pytest.raises(ConnectError):
        migration.connect()


def test_list_migrations_empty(config):
    """Test list_migrations with no migrations."""
    migration = PostgresProvider(config)
    migration.create_table_migration()

    result = migration.list_migrations()
    assert result == []


def test_list_migrations_with_data(config):
    """Test list_migrations with various filters."""
    migration = PostgresProvider(config)
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

    # Test tags filter
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

    migration = PostgresProvider(config)
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

    migration = PostgresProvider(config)
    migration.create_table_migration()

    # First migrate up
    migration.migrate_up(revision)

    # Then migrate down
    result = migration.migrate_down(revision)
    assert result == 1  # Should return rowcount from DELETE

    # Verify revision was removed
    head = migration.get_head_revision()
    assert head is None


def test_get_head_revision_no_table(config):
    """Test get_head_revision when migration table doesn't exist."""
    migration = PostgresProvider(config)
    # Don't create the table

    # Should handle gracefully and return None
    head = migration.get_head_revision()
    assert head is None


def test_migrate_up_return_value(config):
    """Test that migrate_up returns correct rowcount."""
    revision = Revision(
        revision_id="test_return",
        down_revision_id=None,
        message="Test return value",
        up_sql="SELECT 1",
        down_sql="SELECT 2",
    )

    migration = PostgresProvider(config)
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

    migration = PostgresProvider(config)
    migration.create_table_migration()

    # First migrate up
    migration.migrate_up(revision)

    # Then migrate down and check return value
    result = migration.migrate_down(revision)
    assert result == 1  # Should delete exactly one row
