from datetime import datetime

from wandern.models import Revision
from wandern.templates.engine import generate_template, get_environment


def test_get_environment():
    """Test get_environment function returns proper Jinja2 environment."""
    env = get_environment()

    # Test that it returns a SandboxedEnvironment
    assert hasattr(env, "get_template")
    assert hasattr(env, "loader")

    # Test caching - should return same instance
    env2 = get_environment()
    assert env is env2  # Should be the same instance due to @lru_cache


def test_get_environment_can_load_template():
    """Test that the environment can load the migration template."""
    env = get_environment()
    template = env.get_template("migration.sql.j2")
    assert template is not None
    assert hasattr(template, "render")


def test_generate_template_basic():
    """Test generate_template with basic revision data."""
    revision = Revision(
        revision_id="abc123",
        down_revision_id="def456",
        message="test migration",
        author="John Doe",
        tags=["tag1", "tag2"],
        up_sql="CREATE TABLE test (id INTEGER);",
        down_sql="DROP TABLE test;",
        created_at=datetime(2024, 11, 19, 0, 55, 16),
    )

    result = generate_template("migration.sql.j2", revision)

    # Check that all the expected content is in the result
    assert "abc123" in result  # revision_id
    assert "def456" in result  # down_revision_id
    assert "test migration" in result  # message
    assert "John Doe" in result  # author
    assert "tag1, tag2" in result  # tags
    assert "CREATE TABLE test" in result  # up_sql
    assert "DROP TABLE test" in result  # down_sql
    assert "2024-11-19 00:55:16" in result  # created_at

    # Check template structure
    assert "-- UP" in result
    assert "-- DOWN" in result
    assert "Revision ID:" in result
    assert "Revises:" in result
    assert "Message:" in result
    assert "Author:" in result
    assert "Tags:" in result


def test_generate_template_minimal():
    """Test generate_template with minimal revision data."""
    revision = Revision(
        revision_id="minimal123",
        down_revision_id=None,
        message="minimal migration",
        author=None,
        tags=None,
        up_sql=None,
        down_sql=None,
        created_at=datetime(2024, 11, 19, 0, 55, 16),
    )

    result = generate_template("migration.sql.j2", revision)

    # Check that minimal content is present
    assert "minimal123" in result
    assert "minimal migration" in result
    assert "None" in result  # down_revision_id should be None

    # Check that optional fields are handled properly
    assert "Author:" not in result or "None" in result
    assert "Tags:" not in result

    # Check template structure is still intact
    assert "-- UP" in result
    assert "-- DOWN" in result


def test_generate_template_with_none_down_revision():
    """Test generate_template when down_revision_id is None."""
    revision = Revision(
        revision_id="first123",
        down_revision_id=None,
        message="first migration",
        created_at=datetime(2024, 11, 19, 0, 55, 16),
    )

    result = generate_template("migration.sql.j2", revision)

    assert "first123" in result
    assert "first migration" in result
    assert "None" in result  # None should be rendered as "None"


def test_generate_template_empty_strings():
    """Test generate_template with empty strings."""
    revision = Revision(
        revision_id="empty123",
        down_revision_id="",
        message="",
        author="",
        tags=[],
        up_sql="",
        down_sql="",
        created_at=datetime(2024, 11, 19, 0, 55, 16),
    )

    result = generate_template("migration.sql.j2", revision)

    assert "empty123" in result
    # Empty strings and lists should be handled gracefully
    assert "-- UP" in result
    assert "-- DOWN" in result


def test_generate_template_special_characters():
    """Test generate_template with special characters in data."""
    revision = Revision(
        revision_id="special123",
        down_revision_id="parent456",
        message="migration with 'quotes' and \"double quotes\" and <tags>",
        author="John O'Connor",
        tags=["tag-with-dash", "tag_with_underscore", "tag with spaces"],
        up_sql="CREATE TABLE test (name VARCHAR(255) DEFAULT 'O''Connor');",
        down_sql="DROP TABLE test; -- Comment with special chars !@#$%",
        created_at=datetime(2024, 11, 19, 0, 55, 16),
    )

    result = generate_template("migration.sql.j2", revision)

    # Check that special characters are preserved
    assert "special123" in result
    assert "O'Connor" in result
    assert "tag-with-dash" in result
    assert "CREATE TABLE test" in result
    assert "DROP TABLE test" in result


def test_generate_template_long_content():
    """Test generate_template with long SQL content."""
    long_sql = (
        "CREATE TABLE test (\n"
        + "\n".join([f"    column_{i} VARCHAR(255)," for i in range(100)])
        + "\n    id INTEGER PRIMARY KEY\n);"
    )

    revision = Revision(
        revision_id="long123",
        down_revision_id="parent456",
        message="migration with long SQL",
        up_sql=long_sql,
        down_sql="DROP TABLE test;",
        created_at=datetime(2024, 11, 19, 0, 55, 16),
    )

    result = generate_template("migration.sql.j2", revision)

    # Check that long content is preserved
    assert "long123" in result
    assert "column_50" in result  # Check that middle content is there
    assert "column_99" in result  # Check that end content is there
    assert "CREATE TABLE test" in result
