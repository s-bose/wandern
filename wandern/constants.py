from typing import Pattern
import re

DEFAULT_FILE_FORMAT = "{version}_{slug}_{message}"

REGEX_REVISION_ID: Pattern = re.compile(
    r"Revision ID: (?P<revision_id>\w+)\nRevises: (?P<down_revision_id>\w+)"
)

REGEX_MIGRATION_PARSER: Pattern = re.compile(
    r"""
    /\*                                             # Opening comment
    .*?Timestamp:\s*(?P<timestamp>[^\n]+)           # Timestamp
    .*?Revision\s+ID:\s*(?P<revision_id>\w+)        # Revision ID
    .*?Revises:\s*(?P<revises>\w+)                  # Revises
    .*?Message:\s*(?P<message>[^\n]+)               # Message
    (?:.*?Tags:\s*(?P<tags>[^\n]+))?                # Optional Tags
    (?:.*?Author:\s*(?P<author>[^\n]+))?            # Optional Author
    .*?\*/                                          # End of comment
    \s*                                             # Optional whitespace
    --\s*UP\s*\n                                   # UP section header
    (?P<up_sql>.*?)                                # UP SQL content
    --\s*DOWN\s*\n                                # DOWN section header
    (?P<down_sql>.*)                               # DOWN SQL content
    """,
    re.DOTALL | re.VERBOSE,
)


DEFAULT_CONFIG_FILENAME = ".wd.json"
