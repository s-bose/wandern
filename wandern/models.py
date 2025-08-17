from pydantic import BaseModel


class Revision(BaseModel):
    revision_id: str
    down_revision_id: str | None
    message: str
    tags: list[str] | None = []
    author: str | None = None
    up_sql: str | None
    down_sql: str | None
