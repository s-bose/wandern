from typing import Literal, TypedDict
from dataclasses import dataclass, field


@dataclass
class Config:
    dialect: Literal["postgresql"]
    dsn: str

    # various formats
    file_format: str | None = None
    migration_dir: str | None = None
    migration_table: str = field(default="wd_migrations")


class FileTemplateArgs(TypedDict):
    version: str | None
    slug: str | None
    message: str | None
    author: str | None
    prefix: str | None

    # datetime
    epoch: float | None
    year: str | None
    month: str | None
    day: str | None
    hour: str | None
    minute: str | None
    second: str | None
