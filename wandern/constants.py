from typing import Pattern
import re

DEFAULT_FILE_FORMAT = "{version}_{slug}_{message}"

REGEX_REVISION_ID: Pattern = re.compile(
    r"Revision ID: (?P<revision_id>\w+)\nRevises: (?P<down_revision_id>\w+)"
)
