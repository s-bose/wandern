from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from wandern.constants import DEFAULT_FILE_FORMAT


class Config(BaseModel):
    dialect: Literal["postgresql"]
    dsn: str
    migration_dir: str

    # various formats
    file_format: str | None = Field(default=DEFAULT_FILE_FORMAT)
    migration_table: str = Field(default="wd_migrations")


class FileTemplateArgs(TypedDict):
    version: str | None
    slug: str | None
    message: str | None
    author: str | None

    # datetime
    epoch: float | None
    year: str | None
    month: str | None
    day: str | None
    hour: str | None
    minute: str | None
    second: str | None


class Revision(BaseModel):
    revision_id: str
    down_revision_id: str | None
    message: str
    tags: list[str] | None = []
    author: str | None = None
    up_sql: str | None
    down_sql: str | None
