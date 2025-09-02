from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from wandern.exceptions import ConnectError
from wandern.migration import MigrationService
from wandern.models import Config, Revision


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    return Config(
        dsn="sqlite:///test.db",
        migration_dir="/test/migrations",
        file_format="{version}_{slug}_{message}",
        migration_table="test_migrations",
    )


@pytest.fixture
def sample_revision():
    """Create a sample revision for testing."""
    return Revision(
        revision_id="abc123",
        down_revision_id="def456",
        message="test migration",
        author="test author",
        tags=["test"],
        up_sql="CREATE TABLE test (id INTEGER);",
        down_sql="DROP TABLE test;",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_migration_service_init(mock_config):
    """Test MigrationService initialization with full mocking."""
    mock_database = Mock()
    mock_graph = Mock()

    with (
        patch(
            "wandern.migration.get_database_impl", return_value=mock_database
        ) as mock_get_db,
        patch(
            "wandern.migration.MigrationGraph.build", return_value=mock_graph
        ) as mock_graph_build,
    ):
        service = MigrationService(mock_config)

        assert service.config == mock_config
        assert service.database == mock_database
        assert service.graph == mock_graph
        mock_get_db.assert_called_once_with(mock_config.dialect, config=mock_config)
        mock_graph_build.assert_called_once_with(mock_config.migration_dir)


def test_migration_service_init_raises_on_invalid_dsn():
    config = Config(
        dsn="",
        migration_dir="/test/migrations",
        file_format="{version}_{slug}_{message}",
        migration_table="test_migrations",
    )

    with pytest.raises(ConnectError):
        MigrationService(config)


def test_upgrade_first_migration(mock_config, sample_revision):
    """Test upgrade when no migrations have been applied yet."""
    mock_database = Mock()
    mock_database.create_table_migration = Mock()
    mock_database.get_head_revision = Mock(return_value=None)
    mock_database.migrate_up = Mock()

    mock_graph = Mock()
    mock_graph.iter = Mock(return_value=[sample_revision])

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
        patch("wandern.migration.rich.print"),
    ):
        service = MigrationService(mock_config)
        service.upgrade()

        mock_database.create_table_migration.assert_called_once()
        mock_database.get_head_revision.assert_called_once()
        mock_graph.iter.assert_called_once()
        mock_database.migrate_up.assert_called_once_with(sample_revision)


def test_upgrade_with_existing_head(mock_config, sample_revision):
    """Test upgrade when there's already a head revision."""
    head_revision = Revision(
        revision_id="head123",
        down_revision_id=None,
        message="head migration",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    mock_database = Mock()
    mock_database.create_table_migration = Mock()
    mock_database.get_head_revision = Mock(return_value=head_revision)
    mock_database.migrate_up = Mock()

    mock_graph = Mock()
    mock_graph.iter_from = Mock(return_value=[sample_revision])

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
        patch("wandern.migration.rich.print"),
    ):
        service = MigrationService(mock_config)
        service.upgrade()

        mock_graph.iter_from.assert_called_once_with("head123")
        mock_database.migrate_up.assert_called_once_with(sample_revision)


def test_upgrade_with_steps(mock_config):
    """Test upgrade with step limit."""
    revisions = [
        Revision(
            revision_id="rev1",
            down_revision_id=None,
            message="1",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Revision(
            revision_id="rev2",
            down_revision_id="rev1",
            message="2",
            created_at=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        ),
        Revision(
            revision_id="rev3",
            down_revision_id="rev2",
            message="3",
            created_at=datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc),
        ),
    ]

    mock_database = Mock()
    mock_database.create_table_migration = Mock()
    mock_database.get_head_revision = Mock(return_value=None)
    mock_database.migrate_up = Mock()

    mock_graph = Mock()
    mock_graph.iter = Mock(return_value=revisions)

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
        patch("wandern.migration.rich.print"),
    ):
        service = MigrationService(mock_config)
        service.upgrade(steps=2)

        assert mock_database.migrate_up.call_count == 2
        mock_database.migrate_up.assert_any_call(revisions[0])
        mock_database.migrate_up.assert_any_call(revisions[1])


def test_validate_sequential_path_valid(mock_config):
    """Test _validate_sequential_path with valid sequence."""
    head = Revision(
        revision_id="head",
        down_revision_id=None,
        message="head",
        created_at=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )
    revisions = [
        Revision(
            revision_id="rev1",
            down_revision_id="head",
            message="1",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Revision(
            revision_id="rev2",
            down_revision_id="rev1",
            message="2",
            created_at=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        ),
    ]

    mock_database = Mock()
    mock_graph = Mock()

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        # Should not raise any exception
        service._validate_sequential_path(revisions, head)


def test_validate_sequential_path_invalid(mock_config):
    """Test _validate_sequential_path with invalid sequence."""
    head = Revision(
        revision_id="head",
        down_revision_id=None,
        message="head",
        created_at=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )
    revisions = [
        Revision(
            revision_id="rev1",
            down_revision_id="other",
            message="1",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    ]

    mock_database = Mock()
    mock_graph = Mock()

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        with pytest.raises(ValueError, match="Cannot apply migration"):
            service._validate_sequential_path(revisions, head)


def test_downgrade(mock_config):
    """Test downgrade functionality."""
    head_revision = Revision(
        revision_id="current",
        down_revision_id=None,  # No previous revision to break the loop immediately
        message="current migration",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    mock_database = Mock()
    mock_database.get_head_revision = Mock(return_value=head_revision)
    mock_database.migrate_down = Mock()

    mock_graph = Mock()
    mock_graph.get_node = Mock(return_value=head_revision)

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
        patch("wandern.migration.rich.print"),
    ):
        service = MigrationService(mock_config)
        service.downgrade()

        mock_database.migrate_down.assert_called_once_with(head_revision)


def test_downgrade_no_head(mock_config):
    """Test downgrade when no head revision exists."""
    mock_database = Mock()
    mock_database.get_head_revision = Mock(return_value=None)
    mock_database.migrate_down = Mock()

    mock_graph = Mock()

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        service.downgrade()

        # Should return early without doing anything
        mock_database.migrate_down.assert_not_called()


def test_save_migration(mock_config, sample_revision):
    """Test saving migration to file."""
    mock_database = Mock()
    mock_graph = Mock()

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
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
        service = MigrationService(mock_config)
        result = service.save_migration(sample_revision)

        assert result == "test_migration.sql"


def test_filter_migrations(mock_config, sample_revision):
    """Test filtering migrations."""
    mock_database = Mock()
    mock_database.list_migrations = Mock(return_value=[sample_revision])
    mock_graph = Mock()

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        result = service.filter_migrations(author="test", tags=["test"])

        mock_database.list_migrations.assert_called_once_with(
            author="test", tags=["test"], created_at=None
        )
        assert result == [sample_revision]


def test_get_combined_migrations(mock_config):
    """Test getting combined migrations from database and local files."""
    db_revision = Revision(
        revision_id="db_rev",
        down_revision_id=None,
        message="db migration",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    local_revision = Revision(
        revision_id="local_rev",
        down_revision_id="db_rev",
        message="local migration",
        created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )

    mock_database = Mock()
    mock_database.list_migrations = Mock(return_value=[db_revision])

    mock_graph = Mock()
    mock_graph.iter = Mock(return_value=[db_revision, local_revision])

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        result = service.get_combined_migrations()

        # Should return both applied and not applied migrations
        assert len(result) == 2
        assert (db_revision, "applied") in result
        assert (local_revision, "not applied") in result


def test_validate_sequential_path_missing_dependency(mock_config):
    """Test _validate_sequential_path with missing dependency between revisions."""
    head = Revision(
        revision_id="head",
        down_revision_id=None,
        message="head",
        created_at=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )
    revisions = [
        Revision(
            revision_id="rev1",
            down_revision_id="head",
            message="1",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Revision(
            revision_id="rev2",
            down_revision_id="missing",  # This should cause the error
            message="2",
            created_at=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        ),
    ]

    mock_database = Mock()
    mock_graph = Mock()

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        with pytest.raises(ValueError, match="missing dependency between"):
            service._validate_sequential_path(revisions, head)


def test_downgrade_migration_file_not_found(mock_config):
    """Test downgrade when migration file for revision is not found."""
    head_revision = Revision(
        revision_id="missing_file",
        down_revision_id=None,
        message="missing file migration",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    mock_database = Mock()
    mock_database.get_head_revision = Mock(return_value=head_revision)

    mock_graph = Mock()
    mock_graph.get_node = Mock(return_value=None)  # Simulate file not found

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)
        with pytest.raises(
            ValueError, match="Migration file for revision missing_file not found"
        ):
            service.downgrade()


def test_get_combined_migrations_with_filters(mock_config):
    """Test get_combined_migrations with author, tags, and created_at filters."""
    old_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    new_date = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

    db_revision = Revision(
        revision_id="db_rev",
        down_revision_id=None,
        message="db migration",
        author="alice",
        tags=["feature"],
        created_at=new_date,
    )

    # Local revision that should be filtered out by author
    local_revision_wrong_author = Revision(
        revision_id="local_rev1",
        down_revision_id="db_rev",
        message="local migration 1",
        author="bob",  # Different author
        tags=["feature"],
        created_at=new_date,
    )

    # Local revision that should be filtered out by tags
    local_revision_wrong_tags = Revision(
        revision_id="local_rev2",
        down_revision_id="local_rev1",
        message="local migration 2",
        author="alice",
        tags=["bugfix"],  # Different tags
        created_at=new_date,
    )

    # Local revision with no tags (should be filtered out when tags filter is applied)
    local_revision_no_tags = Revision(
        revision_id="local_rev4",
        down_revision_id="local_rev3",
        message="local migration 4",
        author="alice",
        tags=None,  # No tags
        created_at=new_date,
    )

    # Local revision that should be filtered out by created_at
    local_revision_old_date = Revision(
        revision_id="local_rev3",
        down_revision_id="local_rev2",
        message="local migration 3",
        author="alice",
        tags=["feature"],
        created_at=old_date,  # Older than filter
    )

    mock_database = Mock()
    mock_database.list_migrations = Mock(return_value=[db_revision])

    mock_graph = Mock()
    mock_graph.iter = Mock(
        return_value=[
            db_revision,
            local_revision_wrong_author,
            local_revision_wrong_tags,
            local_revision_old_date,
            local_revision_no_tags,
        ]
    )

    with (
        patch("wandern.migration.get_database_impl", return_value=mock_database),
        patch("wandern.migration.MigrationGraph.build", return_value=mock_graph),
    ):
        service = MigrationService(mock_config)

        # Test author filter
        result = service.get_combined_migrations(author="alice")
        local_revisions = [rev for rev, status in result if status == "not applied"]
        assert (
            len(local_revisions) == 3
        )  # Should include only alice's revisions (local_rev2, local_rev3, local_rev4)

        # Test tags filter
        result = service.get_combined_migrations(tags=["feature"])
        local_revisions = [rev for rev, status in result if status == "not applied"]
        assert (
            len(local_revisions) == 2
        )  # Should include feature tagged revisions (local_rev1, local_rev3)

        # Test created_at filter
        result = service.get_combined_migrations(created_at=new_date)
        local_revisions = [rev for rev, status in result if status == "not applied"]
        assert (
            len(local_revisions) == 3
        )  # Should include only revisions >= new_date (local_rev1, local_rev2, local_rev4)
