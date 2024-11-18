from typing import Literal
from dataclasses import dataclass

DEFAULT_FILE_TEMPLATE = "{version}_{description}_{timestamp}.sql"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"  # ISO format


@dataclass
class Config:
    dialect: Literal["postgresql"]
    dsn: str | None = None
    host: str | None = None
    port: str | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    sslmode: str | None = None

    integer_version: bool = False

    # various formats
    file_template: str | None = None
    datetime_format: str | None = None
