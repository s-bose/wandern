from datetime import datetime
from enum import StrEnum

import pytest
from pydantic import ValidationError

from wandern.constants import DEFAULT_FILE_FORMAT, DEFAULT_MIGRATION_TABLE
from wandern.models import Config, DatabaseProviders, FileTemplateArgs, Revision


def test_database_providers_enum():
    """Test DatabaseProviders enum contains expected values"""
    assert DatabaseProviders.POSTGRESQL == "postgresql"
    assert DatabaseProviders.SQLITE == "sqlite"
    assert DatabaseProviders.MYSQL == "mysql"
    assert DatabaseProviders.MSSQL == "mssql"


def test_database_providers_is_str_enum():
    """Test DatabaseProviders is a StrEnum"""
    assert issubclass(DatabaseProviders, StrEnum)
    assert isinstance(DatabaseProviders.POSTGRESQL, str)


def test_config_model_required_fields():
    """Test Config model creation with required fields"""
    config = Config(dsn="sqlite:///test.db", migration_dir="/path/to/migrations")

    assert config.dsn == "sqlite:///test.db"
    assert config.migration_dir == "/path/to/migrations"


def test_config_model_default_values():
    """Test Config model default values for optional fields"""
    config = Config(dsn="sqlite:///test.db", migration_dir="/path/to/migrations")

    assert config.file_format == DEFAULT_FILE_FORMAT
    assert config.migration_table == DEFAULT_MIGRATION_TABLE


def test_config_model_with_optional_fields():
    """Test Config model with custom optional field values"""
    config = Config(
        dsn="postgresql://user:pass@localhost/db",
        migration_dir="/migrations",
        file_format="custom_{version}",
        migration_table="custom_migrations",
    )

    assert config.dsn == "postgresql://user:pass@localhost/db"
    assert config.migration_dir == "/migrations"
    assert config.file_format == "custom_{version}"
    assert config.migration_table == "custom_migrations"


@pytest.mark.parametrize(
    "dsn,expected_dialect",
    [
        ("sqlite:///test.db", DatabaseProviders.SQLITE),
        ("postgresql://user:pass@localhost/db", DatabaseProviders.POSTGRESQL),
        ("mysql://user:pass@localhost/db", DatabaseProviders.MYSQL),
        ("mssql://user:pass@localhost/db", DatabaseProviders.MSSQL),
    ],
)
def test_config_dialect_property(dsn, expected_dialect):
    """Test Config dialect property extracts correct provider from DSN"""
    config = Config(dsn=dsn, migration_dir="/migrations")
    assert config.dialect == expected_dialect


def test_config_dialect_property_invalid_dsn():
    """Test Config dialect property with invalid DSN format"""
    config = Config(dsn="invalid_dsn_format", migration_dir="/migrations")

    with pytest.raises(ValueError):
        _ = config.dialect


def test_config_model_validation_missing_required_fields():
    """Test Config model validation with missing required fields"""
    with pytest.raises(ValidationError):
        Config(dsn="sqlite:///test.db")  # missing migration_dir

    with pytest.raises(ValidationError):
        Config(migration_dir="/migrations")  # missing dsn


def test_file_template_args_structure():
    """Test FileTemplateArgs TypedDict accepts expected structure"""
    # This test is mainly for documentation since TypedDict doesn't enforce at runtime
    template_args: FileTemplateArgs = {
        "version": "v1.0.0",
        "slug": "test_migration",
        "message": "Add users table",
        "author": "test_user",
        "epoch": 1640995200.0,
        "year": "2024",
        "month": "01",
        "day": "15",
        "hour": "10",
        "minute": "30",
        "second": "45",
    }

    # Verify the structure is accepted and accessible
    assert template_args["version"] == "v1.0.0"
    assert template_args["slug"] == "test_migration"
    assert template_args["message"] == "Add users table"
    assert template_args["author"] == "test_user"
    assert template_args["epoch"] == 1640995200.0


def test_file_template_args_nullable_fields():
    """Test FileTemplateArgs with None values for nullable fields"""
    template_args: FileTemplateArgs = {
        "version": None,
        "slug": None,
        "message": None,
        "author": None,
        "epoch": None,
        "year": None,
        "month": None,
        "day": None,
        "hour": None,
        "minute": None,
        "second": None,
    }

    assert all(value is None for value in template_args.values())


def test_revision_model_required_fields():
    """Test Revision model creation with required fields"""
    revision = Revision(
        revision_id="abc123", down_revision_id="def456", message="Add users table"
    )

    assert revision.revision_id == "abc123"
    assert revision.down_revision_id == "def456"
    assert revision.message == "Add users table"


def test_revision_model_with_all_fields():
    """Test Revision model with all fields specified"""
    created_time = datetime(2024, 1, 15, 10, 30, 0)

    revision = Revision(
        revision_id="abc123",
        down_revision_id="def456",
        message="Add users table",
        tags=["feature", "users"],
        author="test_user",
        up_sql="CREATE TABLE users (id INTEGER PRIMARY KEY);",
        down_sql="DROP TABLE users;",
        created_at=created_time,
    )

    assert revision.revision_id == "abc123"
    assert revision.down_revision_id == "def456"
    assert revision.message == "Add users table"
    assert revision.tags == ["feature", "users"]
    assert revision.author == "test_user"
    assert revision.up_sql == "CREATE TABLE users (id INTEGER PRIMARY KEY);"
    assert revision.down_sql == "DROP TABLE users;"
    assert revision.created_at == created_time


def test_revision_model_default_values():
    """Test Revision model default values"""
    revision = Revision(
        revision_id="abc123", down_revision_id="def456", message="Add users table"
    )

    # Default values
    assert revision.tags is None
    assert revision.author is None
    assert revision.up_sql is None
    assert revision.down_sql is None
    assert isinstance(revision.created_at, datetime)


def test_revision_model_nullable_fields():
    """Test Revision model with None values for nullable fields"""
    revision = Revision(
        revision_id="abc123",
        down_revision_id=None,  # Can be None for first revision
        message="Initial migration",
        tags=None,
        author=None,
        up_sql=None,
        down_sql=None,
    )

    assert revision.revision_id == "abc123"
    assert revision.down_revision_id is None
    assert revision.message == "Initial migration"
    assert revision.tags is None
    assert revision.author is None
    assert revision.up_sql is None
    assert revision.down_sql is None


def test_revision_model_validation_missing_required_fields():
    """Test Revision model validation with missing required fields"""
    with pytest.raises(ValidationError):
        Revision(
            down_revision_id="def456", message="Add users table"
        )  # missing revision_id

    with pytest.raises(ValidationError):
        Revision(revision_id="abc123", down_revision_id="def456")  # missing message

    with pytest.raises(ValidationError):
        Revision(
            revision_id="abc123", message="Add users table"
        )  # missing down_revision_id


def test_revision_model_datetime_handling():
    """Test Revision model datetime field handling"""
    # Test with default datetime
    revision1 = Revision(
        revision_id="abc123", down_revision_id="def456", message="Test migration"
    )

    # Test with custom datetime
    custom_time = datetime(2024, 1, 15, 10, 30, 0)
    revision2 = Revision(
        revision_id="xyz789",
        down_revision_id="abc123",
        message="Another migration",
        created_at=custom_time,
    )

    assert isinstance(revision1.created_at, datetime)
    assert revision2.created_at == custom_time


def test_revision_model_tags_empty_list_default():
    """Test Revision model tags field default behavior"""
    # According to the model definition, tags has default=[] but is None
    # This tests the actual behavior
    revision = Revision(
        revision_id="abc123", down_revision_id="def456", message="Test migration"
    )

    # Based on the model definition with default=[] but = None, it should be None
    assert revision.tags is None


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("revision_id", ""),  # empty string
        ("message", ""),  # empty string
        ("up_sql", "SELECT 1;"),  # valid SQL
        ("down_sql", "DROP TABLE test;"),  # valid SQL
        ("author", "user@example.com"),  # email format
        ("tags", ["tag1", "tag2", "tag3"]),  # multiple tags
    ],
)
def test_revision_model_field_variations(field_name, field_value):
    """Test Revision model with various field value combinations"""
    base_data = {
        "revision_id": "abc123",
        "down_revision_id": "def456",
        "message": "Test migration",
    }

    base_data[field_name] = field_value
    revision = Revision(**base_data)

    assert getattr(revision, field_name) == field_value
