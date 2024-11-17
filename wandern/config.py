from typing import TypedDict, Literal


class Config(TypedDict):
    dialect: Literal["postgresql"]
    host: str
    port: str
    database: str
    username: str
    password: str
    sslmode: str

    file_template: str
    integer_version: bool
