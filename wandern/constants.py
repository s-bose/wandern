import re
from typing import Pattern

DEFAULT_FILE_FORMAT = "{version}-{datetime:%Y%m%d_%H%M%S}-{message}"

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
REGEX_MESSAGE: Pattern = re.compile(r"Message:\s*(?P<message>[^\n]*)", re.IGNORECASE)
REGEX_AUTHOR: Pattern = re.compile(r"Author:\s*(?P<author>[^\n]+)", re.IGNORECASE)
REGEX_TAGS: Pattern = re.compile(r"Tags:\s*(?P<tags>[^\n]+)", re.IGNORECASE)


DEFAULT_CONFIG_FILENAME = ".wd.json"
