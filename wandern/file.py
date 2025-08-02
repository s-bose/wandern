from pathlib import Path
import re
from wandern.constants import REGEX_REVISION_ID
from wandern.types import Revision


def parse_sql_file(file_path: str | Path):
    with open(file_path, encoding="utf-8") as file:
        content = file.read()

        sections = re.split(r"^--\s(UP|DOWN)\s*$", content, flags=re.MULTILINE)
        if len(sections) < 5:
            raise ValueError("Invalid file content")

        headers = sections[0].strip()
        match = REGEX_REVISION_ID.search(headers)
        if not match:
            raise ValueError("Invalid version format")

        revision_id, down_revision_id = (
            match.groups()[0].strip(),
            match.groups()[1].strip(),
        )
        up_sql, down_sql = sections[2].strip(), sections[4].strip()

        return Revision(
            revision_id=revision_id,
            down_revision_id=(None if down_revision_id == "None" else down_revision_id),
            up_sql=up_sql.strip(),
            down_sql=down_sql.strip(),
        )
