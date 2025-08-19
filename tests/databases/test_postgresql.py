from datetime import datetime
import psycopg
import pytest
from psycopg.sql import SQL, Identifier
from wandern.databases.postgresql import PostgresMigration
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
    migration = PostgresMigration(config)
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
    migration = PostgresMigration(config)
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
    migration = PostgresMigration(config)
    migration.create_table_migration()

    query = SQL(
        """
        INSERT INTO public.{table}
        VALUES ( %(revision_id)s, %(down_revision_id)s, %(created_at)s )
        """
    ).format(table=Identifier(config.migration_table))

    with psycopg.connect(config.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                {
                    "revision_id": 1,
                    "down_revision_id": None,
                    "created_at": datetime.now(),
                },
            )

    revision = migration.get_head_revision()
    assert revision is not None
    assert revision["revision_id"] == "1"
    assert revision["down_revision_id"] is None


def test_migrate_up(config):
    revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE public.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="DROP TABLE public.users",
    )

    migration = PostgresMigration(config)
    migration.create_table_migration()

    migration.migrate_up(revision)

    revision_db = migration.get_head_revision()
    assert revision_db is not None

    assert revision_db["revision_id"] == "aaaaa"
    assert revision_db["down_revision_id"] is None

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
            cur.execute(revision.down_sql)


def test_migrate_up_multiple_revision(config):
    first_revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE public.users (
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
        up_sql="""CREATE TABLE public.organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="""DROP TABLE public.organizations
        """,
    )
    # Setup
    migration = PostgresMigration(config)
    migration.create_table_migration()

    # Apply migrations
    migration.migrate_up(first_revision)
    migration.migrate_up(second_revision)

    revision = migration.get_head_revision()
    assert revision
    assert revision["revision_id"] == "bbbbb"
    assert revision["down_revision_id"] == "aaaaa"

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

            cur.execute(second_revision.down_sql)
            cur.execute(first_revision.down_sql)


def test_migrate_down(config):
    revision = Revision(
        revision_id="aaaaa",
        down_revision_id=None,
        message="First Revision",
        up_sql="""CREATE TABLE public.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="DROP TABLE public.users",
    )

    migration = PostgresMigration(config)
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
            assert head["revision_id"] == "aaaaa"

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
        up_sql="""CREATE TABLE public.users (
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
        up_sql="""CREATE TABLE public.organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        down_sql="""DROP TABLE public.organizations
        """,
    )

    # Setup
    migration = PostgresMigration(config)
    migration.create_table_migration()

    # Apply migrations
    migration.migrate_up(first_revision)
    migration.migrate_up(second_revision)

    revision = migration.get_head_revision()
    assert revision
    assert revision["revision_id"] == "bbbbb"
    assert revision["down_revision_id"] == "aaaaa"

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
            assert head["revision_id"] == "aaaaa"
            assert head["down_revision_id"] is None

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
