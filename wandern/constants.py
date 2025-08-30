import re
from typing import Pattern

DEFAULT_FILE_FORMAT = "{version}_{slug}_{message}"

DEFAULT_MIGRATION_TABLE = "wd_migrations"

REGEX_MIGRATION_PARSER: Pattern = re.compile(
    r"""
    /\*                                             # Opening comment
    (?P<comment_block>.*?)                          # Capture entire comment block
    \*/                                             # End of comment
    \s*                                             # Optional whitespace
    --\s*UP\s*\n                                   # UP section header
    (?P<up_sql>.*?)                                # UP SQL content
    --\s*DOWN\s*\n                                # DOWN section header
    (?P<down_sql>.*)                               # DOWN SQL content
    """,
    re.DOTALL | re.VERBOSE,
)

# Individual field patterns for extracting fields from comment block
REGEX_TIMESTAMP: Pattern = re.compile(
    r"Timestamp:\s*(?P<timestamp>[^\n]+)", re.IGNORECASE
)
REGEX_REVISION_ID: Pattern = re.compile(
    r"Revision\s+ID:\s*(?P<revision_id>\w+)", re.IGNORECASE
)
REGEX_REVISES: Pattern = re.compile(r"Revises:\s*(?P<revises>\w+)", re.IGNORECASE)
REGEX_MESSAGE: Pattern = re.compile(r"Message:\s*(?P<message>[^\n]+)", re.IGNORECASE)
REGEX_AUTHOR: Pattern = re.compile(r"Author:\s*(?P<author>[^\n]+)", re.IGNORECASE)
REGEX_TAGS: Pattern = re.compile(r"Tags:\s*(?P<tags>[^\n]+)", re.IGNORECASE)


class CompatibleMatch:
    """Backward-compatible match object that provides the same interface as the old regex."""

    def __init__(self, content: str):
        """Initialize from migration content string."""
        self._original_content = content
        self._main_match = REGEX_MIGRATION_PARSER.search(content)

        if not self._main_match:
            raise ValueError("Invalid migration file format")

        # Extract comment block and SQL sections
        comment_block = self._main_match.group("comment_block")
        self._up_sql = self._main_match.group("up_sql")
        self._down_sql = self._main_match.group("down_sql")

        # Extract individual fields from comment block
        timestamp_match = REGEX_TIMESTAMP.search(comment_block)
        revision_id_match = REGEX_REVISION_ID.search(comment_block)
        revises_match = REGEX_REVISES.search(comment_block)
        message_match = REGEX_MESSAGE.search(comment_block)
        author_match = REGEX_AUTHOR.search(comment_block)
        tags_match = REGEX_TAGS.search(comment_block)

        if (
            not timestamp_match
            or not revision_id_match
            or not revises_match
            or not message_match
        ):
            raise ValueError("Missing required fields in migration file")

        # Store field values
        self._fields = {
            "timestamp": (
                timestamp_match.group("timestamp") if timestamp_match else None
            ),
            "revision_id": (
                revision_id_match.group("revision_id") if revision_id_match else None
            ),
            "revises": revises_match.group("revises") if revises_match else None,
            "message": message_match.group("message") if message_match else None,
            "author": author_match.group("author") if author_match else None,
            "tags": tags_match.group("tags") if tags_match else None,
            "up_sql": self._up_sql,
            "down_sql": self._down_sql,
            "comment_block": comment_block,
        }

    def group(self, field_name: str) -> str | None:
        """Get field value by name (backward compatibility)."""
        return self._fields.get(field_name)

    def groupdict(self) -> dict[str, str | None]:
        """Get all fields as dictionary (backward compatibility)."""
        return self._fields.copy()

    def span(self) -> tuple[int, int]:
        """Get match span (backward compatibility)."""
        return self._main_match.span()

    def start(self) -> int:
        """Get match start (backward compatibility)."""
        return self._main_match.start()

    def end(self) -> int:
        """Get match end (backward compatibility)."""
        return self._main_match.end()


def parse_migration_content(content: str) -> CompatibleMatch | None:
    """Parse migration content and return a compatible match object."""
    try:
        return CompatibleMatch(content)
    except ValueError:
        return None


DEFAULT_CONFIG_FILENAME = ".wd.json"
