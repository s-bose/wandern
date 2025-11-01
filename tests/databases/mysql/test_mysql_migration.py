import mysql.connector
from unittest.mock import patch

import networkx as nx
import pytest

from wandern.graph import MigrationGraph
from wandern.migration import MigrationService
from wandern.models import Revision


@pytest.fixture(scope="function", autouse=True)
def truncate_table_migration(config):
    """Run cleanup at the end of function execution"""
    yield

    # For MySQL, parse DSN and clean up
    from wandern.databases.mysql import parse_params_from_dsn, validate_parsed_params
    
    params = parse_params_from_dsn(config.dsn)
    validated_params = validate_parsed_params(params)
    
    conn = mysql.connector.connect(**validated_params)
    cursor = conn.cursor()
    
    # Check if migration table exists and truncate it
    cursor.execute(
        f"""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
        AND table_name = '{config.migration_table}'
        """
    )
    result = cursor.fetchone()
    if result and result[0] > 0:
        cursor.execute(f"DELETE FROM {config.migration_table}")
    
    conn.commit()
    cursor.close()
    conn.close()


@pytest.fixture(scope="function")
def revisions() -> list[Revision]:
    return [
        Revision(
            revision_id="0001",
            down_revision_id=None,
            message="1st commit",
            author="Foo",
            up_sql="SELECT 1 + 1",
            down_sql="SELECT 2 - 1",
        ),
        Revision(
            revision_id="0002",
            down_revision_id="0001",
            message="2nd commit",
            author="Bar",
            up_sql="SELECT 2 + 2",
            down_sql="SELECT 4 - 2",
        ),
        Revision(
            revision_id="0003",
            down_revision_id="0002",
            message="3rd commit",
            author="Baz",
            up_sql="SELECT 3 + 3",
            down_sql="SELECT 6 - 3",
        ),
    ]


def test_upgrade_all(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)
        migration_service.upgrade()

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0003"


def test_upgrade_with_steps(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # Apply only first 2 migrations
        migration_service.upgrade(steps=2)

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0002"  # Should stop at 2nd migration

        # Apply one more step
        migration_service.upgrade(steps=1)

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0003"  # Should now be at 3rd migration


def test_upgrade_with_author_filter(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # Apply migrations only by author "Foo"
        migration_service.upgrade(author="Foo")

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        # Should apply only the migration by Foo (0001)
        assert revision.revision_id == "0001"


def test_upgrade_with_tags_filter(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # Test with non-existent tags (should apply no migrations since fixtures have no tags)
        migration_service.upgrade(tags=["test-tag"])

        revision = migration_service.database.get_head_revision()
        # Should be None since no migrations have the "test-tag"
        assert revision is None


def test_downgrade_all(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # First apply all migrations
        migration_service.upgrade()
        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0003"

        # Then downgrade all
        migration_service.downgrade()

        revision = migration_service.database.get_head_revision()
        # Should be None after complete downgrade
        assert revision is None


def test_downgrade_with_steps(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # First apply all migrations
        migration_service.upgrade()
        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0003"

        # Downgrade 1 step
        migration_service.downgrade(steps=1)

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0002"  # Should be at 2nd migration

        # Downgrade 1 more step
        migration_service.downgrade(steps=1)

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0001"  # Should be at 1st migration


def test_filter_migrations(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # Apply some migrations first
        migration_service.upgrade(steps=2)

        # Filter by author
        migrations = migration_service.filter_migrations(author="Foo")
        assert len(migrations) == 1  # Only one migration by Foo (0001)
        assert all(m.author == "Foo" for m in migrations)

        # Filter by non-existent author
        migrations = migration_service.filter_migrations(author="NonExistent")
        assert len(migrations) == 0

        # Filter without any criteria (should return all applied migrations)
        migrations = migration_service.filter_migrations()
        assert len(migrations) == 2  # Should have 2 applied migrations


def test_get_combined_migrations(config, revisions):
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create a mock graph from revisions fixture
        graph = nx.DiGraph()
        for rev in revisions:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # Create the migration table first
        migration_service.database.create_table_migration()

        # Initially no migrations applied
        combined = migration_service.get_combined_migrations()
        # Should have 3 total migrations, all "not applied"
        assert len(combined) == 3
        assert all(status == "not applied" for _, status in combined)

        # Apply first 2 migrations
        migration_service.upgrade(steps=2)

        combined = migration_service.get_combined_migrations()
        # Should have 3 total migrations: 2 applied, 1 not applied
        assert len(combined) == 3
        applied_count = sum(1 for _, status in combined if status == "applied")
        not_applied_count = sum(1 for _, status in combined if status == "not applied")
        assert applied_count == 2
        assert not_applied_count == 1

        # Filter by author
        combined = migration_service.get_combined_migrations(author="Foo")
        # Should only show migrations by Foo
        foo_migrations = [rev for rev, _ in combined if rev.author == "Foo"]
        assert len(foo_migrations) == 1  # Only 1 migration by Foo (0001)


def test_save_migration(config, revisions):
    """Test saving migration to file."""
    with patch.object(MigrationGraph, "build") as mock_build:
        graph = nx.DiGraph()
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        with (
            patch(
                "wandern.migration.generate_migration_filename",
                return_value="test_migration.sql",
            ),
            patch(
                "wandern.migration.generate_template",
                return_value="-- migration content",
            ),
            patch("builtins.open", create=True),
            patch("os.path.join", return_value="/test/migrations/test_migration.sql"),
            patch("os.path.abspath", return_value="/test/migrations"),
        ):
            result = migration_service.save_migration(revisions[0])
            assert result == "test_migration.sql"


def test_upgrade_with_author_and_tags_validation(config, revisions):
    """Test upgrade with author/tags filter triggers validation."""
    with patch.object(MigrationGraph, "build") as mock_build:
        # Create revisions with tags
        revisions_with_tags = [
            Revision(
                revision_id="0001",
                down_revision_id=None,
                message="1st commit",
                author="Foo",
                tags=["feature"],
                up_sql="SELECT 1",
                down_sql="SELECT 1",
            ),
            Revision(
                revision_id="0002",
                down_revision_id="0001",
                message="2nd commit",
                author="Bar",
                tags=["bugfix"],
                up_sql="SELECT 2",
                down_sql="SELECT 2",
            ),
        ]

        graph = nx.DiGraph()
        for rev in revisions_with_tags:
            graph.add_node(rev.revision_id, **rev.model_dump())
        for rev in revisions_with_tags:
            if rev.down_revision_id:
                graph.add_edge(rev.down_revision_id, rev.revision_id)
        mock_build.return_value = MigrationGraph(graph)

        migration_service = MigrationService(config)

        # This should trigger validation path
        migration_service.upgrade(tags=["feature"])

        revision = migration_service.database.get_head_revision()
        assert revision is not None
        assert revision.revision_id == "0001"  # Only feature tagged migration
