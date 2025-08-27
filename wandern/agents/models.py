from pydantic import BaseModel
from typing import Generic, TypeVar


_DataT = TypeVar("_DataT", bound=BaseModel)
_ErrorT = TypeVar("_ErrorT")


class AgentResponse(BaseModel, Generic[_DataT, _ErrorT]):
    data: _DataT
    message: str | None = None
    error: _ErrorT | None = None
