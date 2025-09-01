from wandern.constants import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_FILE_FORMAT,
    DEFAULT_MIGRATION_TABLE,
    REGEX_AUTHOR,
    REGEX_MESSAGE,
    REGEX_MIGRATION_PARSER,
    REGEX_REVISES,
    REGEX_REVISION_ID,
    REGEX_TAGS,
    REGEX_TIMESTAMP,
)


def test_default_constants():
    """Test that default constants have expected values."""
    assert DEFAULT_FILE_FORMAT == "{version}-{datetime:%Y%m%d_%H%M%S}-{message}"
    assert DEFAULT_MIGRATION_TABLE == "wd_migrations"
    assert DEFAULT_CONFIG_FILENAME == ".wd.json"


def test_regex_pattern_type():
    """Test that REGEX_MIGRATION_PARSER is a compiled regex pattern."""
    import re

    assert isinstance(REGEX_MIGRATION_PARSER, type(re.compile(r"")))
    assert REGEX_MIGRATION_PARSER.flags & re.DOTALL
    assert REGEX_MIGRATION_PARSER.flags & re.VERBOSE


def test_individual_regex_patterns():
    """Test individual regex patterns work correctly."""
    # Test REGEX_TIMESTAMP
    content = "Some text\nTimestamp: 2024-11-19 15:30:45\nOther text"
    match = REGEX_TIMESTAMP.search(content)
    assert match is not None
    assert match.group("timestamp") == "2024-11-19 15:30:45"

    # Test case insensitive
    content_lower = "timestamp: 2024-11-19 15:30:45"
    match = REGEX_TIMESTAMP.search(content_lower)
    assert match is not None
    assert match.group("timestamp") == "2024-11-19 15:30:45"

    # Test REGEX_REVISION_ID
    content = "Revision ID: abc123"
    match = REGEX_REVISION_ID.search(content)
    assert match is not None
    assert match.group("revision_id") == "abc123"

    # Test with space variations
    content = "Revision   ID:def456"
    match = REGEX_REVISION_ID.search(content)
    assert match is not None
    assert match.group("revision_id") == "def456"

    # Test REGEX_REVISES
    content = "Revises: previous_rev"
    match = REGEX_REVISES.search(content)
    assert match is not None
    assert match.group("revises") == "previous_rev"

    # Test REGEX_MESSAGE
    content = "Message: This is a test migration message"
    match = REGEX_MESSAGE.search(content)
    assert match is not None
    assert match.group("message") == "This is a test migration message"

    # Test REGEX_AUTHOR
    content = "Author: John Doe <john@example.com>"
    match = REGEX_AUTHOR.search(content)
    assert match is not None
    assert match.group("author") == "John Doe <john@example.com>"

    # Test REGEX_TAGS
    content = "Tags: tag1, tag2, tag3"
    match = REGEX_TAGS.search(content)
    assert match is not None
    assert match.group("tags") == "tag1, tag2, tag3"


def test_individual_regex_patterns_no_match():
    """Test individual regex patterns return None when no match found."""
    no_match_content = "Some random text without any patterns"

    assert REGEX_TIMESTAMP.search(no_match_content) is None
    assert REGEX_REVISION_ID.search(no_match_content) is None
    assert REGEX_REVISES.search(no_match_content) is None
    assert REGEX_MESSAGE.search(no_match_content) is None
    assert REGEX_AUTHOR.search(no_match_content) is None
    assert REGEX_TAGS.search(no_match_content) is None


def test_regex_patterns_with_edge_cases():
    """Test regex patterns with various edge cases and formatting."""
    # Test timestamp with different formats
    timestamp_cases = [
        "Timestamp: 2024-01-01 00:00:00",
        "timestamp: 2024-12-31 23:59:59",
        "TIMESTAMP: 2024-06-15 12:30:45",
        "Timestamp:2024-11-19 15:30:45",  # No space after colon
        "Timestamp:  2024-11-19 15:30:45",  # Multiple spaces
    ]

    for case in timestamp_cases:
        match = REGEX_TIMESTAMP.search(case)
        assert match is not None, f"Failed to match: {case}"
        assert "2024-" in match.group("timestamp")

    # Test revision ID with different formats
    revision_cases = [
        "Revision ID: abc123",
        "revision id: def456",
        "REVISION ID: xyz789",
        "Revision ID:test123",  # No space after colon
        "Revision   ID: spaced123",  # Multiple spaces in field name
    ]

    for case in revision_cases:
        match = REGEX_REVISION_ID.search(case)
        assert match is not None, f"Failed to match: {case}"
        assert match.group("revision_id") is not None

    # Test message with special characters and line endings
    message_cases = [
        "Message: Simple message",
        "message: Message with special chars: @#$%^&*()",
        "MESSAGE: Message ending with newline\n",
        "Message: Message with numbers 123 and symbols !@#",
        "Message:No space after colon",
    ]

    for case in message_cases:
        match = REGEX_MESSAGE.search(case)
        assert match is not None, f"Failed to match: {case}"
        assert match.group("message") is not None
