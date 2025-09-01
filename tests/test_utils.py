import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import typer

from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.models import Config
from wandern.utils import (
    create_empty_migration,
    generate_migration_filename,
    generate_revision_id,
    load_config,
    parse_sql_file_content,
    save_config,
    slugify,
)


def test_slugify():
    """Test slugify function with various inputs."""
    assert slugify("hello world") == "uU0nuZNNPg"
    assert slugify("test message", length=5) == "Pwo3e"
    assert slugify("special!@#$%chars") == "JF6dDOXDj2"
    assert slugify("") == "47DEQpj8HB"

    # Test length parameter
    assert len(slugify("very long message", length=15)) <= 15
    assert len(slugify("short", length=20)) <= 20


def test_generate_migration_filename():
    """Test migration filename generation with various formats."""
    # Test basic format
    current_datetime = datetime.now(timezone.utc)
    result = generate_migration_filename(
        fmt="{day:02}_{month:02}_{year}__{version}__{message}",
        version="0001",
        message="test",
    )
    expected = f"{current_datetime.day:02}_{current_datetime.month:02}_{current_datetime.year}__1__test.sql"
    assert result == expected

    # Test default format
    result = generate_migration_filename(
        fmt=DEFAULT_FILE_FORMAT, version="0001", message="test message"
    )
    assert result.endswith(".sql")
    assert "1" in result
    assert "test_message" in result

    # Test with author
    result = generate_migration_filename(
        fmt="{version}_{author}_{slug}", version="0002", message="test", author="john"
    )
    assert "2" in result
    assert "john" in result

    # Test numeric version conversion
    result = generate_migration_filename(
        fmt="{version}", version="0005", message="test"
    )
    assert "5" in result

    # Test non-numeric version
    result = generate_migration_filename(
        fmt="{version}", version="abc123", message="test"
    )
    assert "abc123" in result


def test_generate_migration_filename_errors():
    """Test error cases for generate_migration_filename."""
    # Missing required fields
    with pytest.raises(ValueError, match="version or slug or message is required"):
        generate_migration_filename(fmt="{other}", version="", message="")

    # Missing fields in format
    with pytest.raises(ValueError, match="Missing required fields"):
        generate_migration_filename(fmt="{nonexistent}", version="1", message="test")


def test_generate_migration_filename_edge_cases():
    """Test edge cases for generate_migration_filename."""
    # Test when filename already ends with .sql
    result = generate_migration_filename(
        fmt="{version}_{message}.sql", version="0001", message="test"
    )
    assert result.endswith(".sql")
    assert result.count(".sql") == 1  # Should not double-append

    # Test with None message but valid slug generation
    result = generate_migration_filename(
        fmt="{version}_{slug}", version="0001", message=None
    )
    assert "1" in result
    assert result.endswith(".sql")

    # Test with empty message
    result = generate_migration_filename(fmt="{version}", version="0001", message="")
    assert "1" in result

    # Test with all template variables
    result = generate_migration_filename(
        fmt="{year}_{month}_{day}_{hour}_{minute}_{second}_{epoch}_{version}_{author}_{slug}_{message}",
        version="0001",
        message="test migration",
        author="john_doe",
    )
    assert "john_doe" in result
    assert "test_migration" in result


def test_generate_revision_id():
    """Test revision ID generation."""
    rev_id = generate_revision_id()
    assert len(rev_id) == 8
    assert all(c in "0123456789abcdef" for c in rev_id)


def test_generate_revision_id_uniqueness():
    """Test uniqueness of generated revision IDs."""
    revs = [generate_revision_id() for _ in range(100)]
    assert len(revs) == len(set(revs))


def test_create_empty_migration():
    """Test empty migration creation."""
    # Basic migration
    revision = create_empty_migration(
        message="test migration", down_revision_id="abc123"
    )
    assert revision.message == "test migration"
    assert revision.down_revision_id == "abc123"
    assert revision.up_sql is None
    assert revision.down_sql is None
    assert len(revision.revision_id) == 8
    assert isinstance(revision.created_at, datetime)

    # Migration with optional fields
    revision = create_empty_migration(
        message="test with options",
        down_revision_id=None,
        author="test author",
        tags=["tag1", "tag2"],
    )
    assert revision.author == "test author"
    assert revision.tags == ["tag1", "tag2"]
    assert revision.down_revision_id is None

    # Migration with empty message
    revision = create_empty_migration(message=None, down_revision_id="abc")
    assert revision.message == ""


def test_parse_sql_file_content_full():
    """Test parsing SQL file content fully."""
    content = """/*
    Timestamp: 2024-11-19 00:55:16
    Revision ID: abc123
    Revises: def456
    Message: test migration
    Author: John Doe
    Tags: tag1, tag2
    */

    -- UP
    CREATE TABLE test (id INTEGER);

    -- DOWN
    DROP TABLE test;
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()

        try:
            revision = parse_sql_file_content(f.name)
            assert revision.revision_id == "abc123"
            assert revision.down_revision_id == "def456"
            assert revision.message == "test migration"
            assert revision.author == "John Doe"
            assert revision.tags == [
                "tag1",
                " tag2",
            ]  # Note: there's a space before tag2
            assert revision.up_sql and "CREATE TABLE test" in revision.up_sql
            assert revision.down_sql and "DROP TABLE test" in revision.down_sql
            assert isinstance(revision.created_at, datetime)
        finally:
            os.unlink(f.name)


def test_parse_sql_file_content_minimal():
    """Test parsing SQL file with minimal content."""
    content = """/*
    Timestamp: 2024-11-19 00:55:16
    Revision ID: abc123
    Revises: none
    Message: minimal migration
    */

    -- UP

    -- DOWN
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()

        try:
            revision = parse_sql_file_content(f.name)
            assert revision.revision_id == "abc123"
            assert revision.down_revision_id is None
            assert revision.message == "minimal migration"
            assert revision.author is None
            assert revision.tags is None
        finally:
            os.unlink(f.name)


def test_parse_sql_file_content_invalid():
    """Test parsing invalid SQL file content."""
    content = "Invalid content without proper format"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()

        try:
            with pytest.raises(ValueError, match="Invalid migration file format"):
                parse_sql_file_content(f.name)
        finally:
            os.unlink(f.name)


def test_parse_sql_file_content_missing_fields():
    """Test parsing SQL file with missing required fields."""
    # Missing timestamp
    content = """/*
    Revision ID: abc123
    Revises: none
    Message: test migration
    */
    -- UP
    -- DOWN
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()
        try:
            with pytest.raises(ValueError, match="Timestamp field is required"):
                parse_sql_file_content(f.name)
        finally:
            os.unlink(f.name)

    # Missing revision ID
    content = """/*
    Timestamp: 2024-11-19 00:55:16
    Revises: none
    Message: test migration
    */
    -- UP
    -- DOWN
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()
        try:
            with pytest.raises(ValueError, match="Revision ID field is required"):
                parse_sql_file_content(f.name)
        finally:
            os.unlink(f.name)

    # Missing revises field
    content = """/*
    Timestamp: 2024-11-19 00:55:16
    Revision ID: abc123
    Message: test migration
    */
    -- UP
    -- DOWN
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()
        try:
            with pytest.raises(ValueError, match="Revises field is required"):
                parse_sql_file_content(f.name)
        finally:
            os.unlink(f.name)

    # Missing message field
    content = """/*
    Timestamp: 2024-11-19 00:55:16
    Revision ID: abc123
    Revises: none
    */
    -- UP
    -- DOWN
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(content)
        f.flush()
        try:
            with pytest.raises(ValueError, match="Message field is required"):
                parse_sql_file_content(f.name)
        finally:
            os.unlink(f.name)


def test_load_config():
    """Test loading configuration from file."""
    config_data = {
        "dsn": "sqlite:///test.db",
        "migration_dir": "./test_migrations",
        "file_format": "{version}_{message}",
        "migration_table": "migrations",
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".wd.json"
        migration_dir = Path(temp_dir) / "test_migrations"
        migration_dir.mkdir()

        # Update config to use absolute path
        config_data["migration_dir"] = str(migration_dir)

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        config = load_config(config_path)
        assert config.dsn == "sqlite:///test.db"
        assert (
            config.dialect.value == "sqlite"
        )  # dialect is a property that returns DatabaseProviders enum
        assert config.migration_dir == str(migration_dir)
        assert config.file_format == "{version}_{message}"
        assert config.migration_table == "migrations"


def test_load_config_nonexistent():
    """Test loading config from nonexistent file."""
    with pytest.raises(typer.Exit):
        load_config("/nonexistent/path/.wd.json")


def test_load_config_unwriteable_migration_dir():
    """Test loading config with unwriteable migration directory."""
    config_data = {
        "dsn": "sqlite:///test.db",
        "migration_dir": "/read-only-path",
        "file_format": "{version}_{message}",
        "migration_table": "migrations",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        f.flush()

        try:
            with pytest.raises(typer.Exit):
                load_config(f.name)
        finally:
            os.unlink(f.name)


def test_load_config_invalid_json():
    """Test loading config with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("invalid json content {")
        f.flush()

        try:
            with pytest.raises(json.JSONDecodeError):
                load_config(f.name)
        finally:
            os.unlink(f.name)


def test_save_config_error_handling():
    """Test save_config with error conditions."""
    config = Config(
        dsn="postgresql://user:pass@localhost/db",
        migration_dir="./migrations",
    )

    # Test saving to a directory that doesn't exist
    nonexistent_dir = "/nonexistent/directory/config.json"
    with pytest.raises((FileNotFoundError, PermissionError, OSError)):
        save_config(config, nonexistent_dir)


def test_save_config():
    """Test saving configuration to file."""
    config = Config(
        dsn="postgresql://user:pass@localhost/db",
        migration_dir="./migrations",
        file_format="{version}_{slug}",
        migration_table="wd_migrations",
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        try:
            save_config(config, f.name)

            # Verify file was written correctly
            with open(f.name, "r") as rf:
                saved_data = json.load(rf)
                assert saved_data["dsn"] == "postgresql://user:pass@localhost/db"
                assert saved_data["migration_dir"] == "./migrations"
                assert saved_data["file_format"] == "{version}_{slug}"
                assert saved_data["migration_table"] == "wd_migrations"
        finally:
            os.unlink(f.name)
