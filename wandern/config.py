from typing import Literal
from dataclasses import dataclass


@dataclass
class Config:
    dialect: Literal["postgresql"]
    host: str
    port: str
    database: str
    username: str
    password: str
    sslmode: str

    file_template: str
    integer_version: bool
