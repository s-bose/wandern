import pytest
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from wandern.cli.utils import (
    date_validator,
    create_migration_table,
    create_filter_panel,
    display_migrations_state,
)
from wandern.models import Revision


def test_date_validator():
    """Test date_validator function with various inputs."""
    # Valid dates
    assert date_validator("2024-01-01") is True
    assert date_validator("2023-12-31") is True
    assert date_validator("2024-02-29") is True  # Leap year

    # Invalid dates
    assert date_validator("invalid-date") is False
    assert date_validator("2024-13-01") is False  # Invalid month
    assert date_validator("2024-01-32") is False  # Invalid day
    assert date_validator("2023-02-29") is False  # Not a leap year
    assert date_validator("") is False
    assert date_validator("2024/01/01") is False  # Wrong format


def test_create_migration_table_empty():
    """Test create_migration_table with empty revisions list."""
    table = create_migration_table([])

    assert isinstance(table, Table)
    # Check that it has the expected columns
    assert len(table.columns) == 5  # ID, Message, Author, Tags, Date


def test_create_migration_table_with_sources():
    """Test create_migration_table with sources (status column)."""
    table = create_migration_table([], sources=["applied"])

    assert isinstance(table, Table)
    # Should have 6 columns when sources are provided
    assert len(table.columns) == 6  # ID, Message, Author, Tags, Date, Status


def test_create_migration_table_with_revisions():
    """Test create_migration_table with actual revisions."""
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="First migration",
            author="test_user",
            tags=["feature", "db"],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        ),
        Revision(
            revision_id="def67890",
            down_revision_id="abc12345",
            message="Second migration",
            author="another_user",
            tags=["bugfix"],
            created_at=datetime(2024, 1, 16, 14, 45, 0),
        ),
    ]

    table = create_migration_table(revisions)

    assert isinstance(table, Table)
    assert len(table.columns) == 5
    # The table should have rows for the revisions


def test_create_migration_table_with_db_head():
    """Test create_migration_table with database head indicator."""
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="First migration",
            author="test_user",
            tags=["feature"],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
    ]

    table = create_migration_table(revisions, db_head_id="abc12345")

    assert isinstance(table, Table)
    # The table should be created successfully with head indicator


def test_create_migration_table_with_sources_and_revisions():
    """Test create_migration_table with both revisions and sources."""
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="Test migration",
            author="test_user",
            tags=["test"],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
    ]
    sources = ["applied"]

    table = create_migration_table(revisions, sources=sources)

    assert isinstance(table, Table)
    assert len(table.columns) == 6  # Should include Status column


def test_create_filter_panel_no_filters():
    """Test create_filter_panel with no active filters."""
    panel = create_filter_panel(None, None, None)

    assert isinstance(panel, Panel)


def test_create_filter_panel_with_author():
    """Test create_filter_panel with author filter."""
    panel = create_filter_panel("test_author", None, None)

    assert isinstance(panel, Panel)


def test_create_filter_panel_with_tags():
    """Test create_filter_panel with tags filter."""
    panel = create_filter_panel(None, ["feature", "bugfix"], None)

    assert isinstance(panel, Panel)


def test_create_filter_panel_with_date():
    """Test create_filter_panel with date filter."""
    test_date = datetime(2024, 1, 15)
    panel = create_filter_panel(None, None, test_date)

    assert isinstance(panel, Panel)


def test_create_filter_panel_with_all_filters():
    """Test create_filter_panel with all filters active."""
    test_date = datetime(2024, 1, 15)
    panel = create_filter_panel("test_author", ["feature", "bugfix"], test_date)

    assert isinstance(panel, Panel)


def test_display_migrations_state_basic():
    """Test display_migrations_state with basic parameters."""
    console = Console(file=None)  # Don't output to stdout during tests
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="Test migration",
            author="test_user",
            tags=["test"],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
    ]

    # This should not raise any errors
    try:
        display_migrations_state(
            console=console,
            filtered_revisions=revisions,
            author_filter=None,
            tags_filter=None,
            date_filter=None,
        )
    except Exception as e:
        pytest.fail(f"display_migrations_state raised an exception: {e}")


def test_display_migrations_state_with_filters():
    """Test display_migrations_state with all filters."""
    console = Console(file=None)  # Don't output to stdout during tests
    revisions = []
    test_date = datetime(2024, 1, 15)

    # This should not raise any errors
    try:
        display_migrations_state(
            console=console,
            filtered_revisions=revisions,
            author_filter="test_author",
            tags_filter=["feature"],
            date_filter=test_date,
            sources=["applied"],
            db_head_id="abc123",
        )
    except Exception as e:
        pytest.fail(f"display_migrations_state raised an exception: {e}")


def test_create_migration_table_with_none_values():
    """Test create_migration_table handles None values gracefully."""
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="",  # Empty message (message is required, can't be None)
            author=None,  # None author (this is allowed)
            tags=None,  # None tags (this is allowed)
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
    ]

    table = create_migration_table(revisions)

    assert isinstance(table, Table)
    # Should handle None values without errors


def test_create_migration_table_with_empty_tags():
    """Test create_migration_table handles empty tags list."""
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="Test migration",
            author="test_user",
            tags=[],  # Empty tags list
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
    ]

    table = create_migration_table(revisions)

    assert isinstance(table, Table)
    # Should handle empty tags without errors


def test_create_migration_table_multiple_revisions_with_sources():
    """Test create_migration_table with multiple revisions and sources to cover status logic for all revisions."""
    revisions = [
        Revision(
            revision_id="abc12345",
            down_revision_id=None,
            message="First migration",
            author="user1",
            tags=["feature"],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        ),
        Revision(
            revision_id="def67890",
            down_revision_id="abc12345",
            message="Second migration",
            author="user2",
            tags=["bugfix"],
            created_at=datetime(2024, 1, 16, 14, 45, 0),
        ),
        Revision(
            revision_id="ghi11111",
            down_revision_id="def67890",
            message="Third migration",
            author="user3",
            tags=["enhancement"],
            created_at=datetime(2024, 1, 17, 16, 20, 0),
        ),
    ]
    # Test with mixed statuses to cover both "applied" and "not applied" cases
    sources = ["applied", "applied", "not_applied"]

    table = create_migration_table(revisions, sources=sources)

    assert isinstance(table, Table)
    assert len(table.columns) == 6  # Should include Status column
