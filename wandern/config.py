from typing import TypedDict, Literal


class Config(TypedDict):
    dialect: Literal["postgresql"]
    host: str
    port: int
    database: str
    username: str
    password: str
    sslmode: str
