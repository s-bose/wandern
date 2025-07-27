from typing import Pattern
import re

MIGRATION_DEFAULT_TABLE_NAME = "wandern_migrations"
TEMPLATE_DEFAULT_FILENAME = "{version}_{slug}_{message}"

REGEX_REVISION_ID: Pattern = re.compile(
    r"Revision ID: (?P<revision_id>\w+)\nRevises: (?P<down_revision_id>\w+)"
)
