from datetime import datetime
from enum import StrEnum
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field

from wandern.constants import DEFAULT_FILE_FORMAT, DEFAULT_MIGRATION_TABLE


class DatabaseProviders(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"  # FUTURE: not implemented
    MSSQL = "mssql"  # FUTURE: not implemented


class Config(BaseModel):
    dsn: str
    migration_dir: str

    # various formats
    file_format: str | None = Field(default=DEFAULT_FILE_FORMAT)
    migration_table: str = Field(default=DEFAULT_MIGRATION_TABLE)

    @property
    def dialect(self):
        _dialect = self.dsn.split("://")[0]
        if _dialect:
            return DatabaseProviders(_dialect)


class FileTemplateArgs(TypedDict):
    version: str | None
    slug: str | None
    message: str | None
    author: str | None

    # datetime
    epoch: float | None
    datetime: datetime | None


class Revision(BaseModel):
    revision_id: Annotated[
        str, Field(description="The unique identifier for the revision")
    ]
    down_revision_id: Annotated[
        str | None,
        Field(
            description=(
                "The identifier of the previous revision, if any, "
                "null if this is the first revision"
            )
        ),
    ]
    message: Annotated[
        str, Field(description="Brief description of what the revision is about")
    ]
    tags: Annotated[
        list[str] | None,
        Field(default=[], description="List of tags associated with the revision"),
    ] = None
    author: Annotated[str | None, Field(description="The author of the revision")] = (
        None
    )
    up_sql: Annotated[
        str | None, Field(description="The SQL to apply the revision")
    ] = None
    down_sql: Annotated[
        str | None, Field(description="The SQL to revert the revision")
    ] = None
    created_at: Annotated[
        datetime,
        Field(
            default_factory=datetime.now,
            description="Time when the revision was created",
        ),
    ] = datetime.now()
