from typing import TypedDict


class Revision(TypedDict):
    revision_id: str
    down_revision_id: str | None
    up_sql: str
    down_sql: str
