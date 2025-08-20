from typing import Literal, TypedDict
from dataclasses import dataclass, field

from wandern.constants import DEFAULT_FILE_FORMAT


@dataclass
class Config:
    dialect: Literal["postgresql"]
    dsn: str
    migration_dir: str

    # various formats
    file_format: str | None = field(default=DEFAULT_FILE_FORMAT)
    migration_table: str = field(default="wd_migrations")


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
