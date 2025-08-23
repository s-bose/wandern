from pydantic import BaseModel
from typing import Generic, TypeVar

from wandern.models import Revision

_DataT = TypeVar("_DataT", bound=BaseModel)
_ErrorT = TypeVar("_ErrorT")


class AgentResponse(BaseModel, Generic[_DataT, _ErrorT]):
    data: _DataT
    error: _ErrorT | None = None


class MigrationAgentResponse(AgentResponse[Revision, str]):
    pass
