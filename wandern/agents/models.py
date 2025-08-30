from typing import Generic, TypeVar

from pydantic import BaseModel

_DataT = TypeVar("_DataT", bound=BaseModel)
_ErrorT = TypeVar("_ErrorT")


class AgentResponse(BaseModel, Generic[_DataT, _ErrorT]):
    data: _DataT
    message: str | None = None
    error: _ErrorT | None = None
