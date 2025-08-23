import os
import rich
from abc import abstractmethod
from typing import Sequence, Generic, TypeVar
from pydantic_ai.agent import Agent
from pydantic_ai.models import Model
from pydantic_ai.tools import Tool
from pydantic_ai.settings import ModelSettings
from pydantic import BaseModel

_DataT = TypeVar("_DataT", bound=BaseModel)
_ErrorT = TypeVar("_ErrorT")


class AgentResponse(BaseModel, Generic[_DataT, _ErrorT]):
    data: _DataT
    message: str | None = None
    error: _ErrorT | None = None


def create_model() -> Model:
    if os.getenv("OPENAI_API_KEY"):
        try:
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider

            openai_provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
            return OpenAIModel(model_name="gpt-4o", provider=openai_provider)
        except ImportError:
            print("Please install openai dependencies with `wandern[openai]`")
            raise
    elif os.getenv("GOOGLE_API_KEY"):
        try:
            from pydantic_ai.models.google import GoogleModel
            from pydantic_ai.providers.google import GoogleProvider

            google_provider = GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY"))
            return GoogleModel(model_name="gemini-2.5-flash", provider=google_provider)
        except ImportError:
            print("Please install google dependencies with `wandern[google]`")
            raise
    else:
        raise ValueError(
            "No supported API key found, please set either `OPENAI_API_KEY` or `GOOGLE_API_KEY`"
        )


class BaseAgent(Generic[_DataT, _ErrorT]):
    def __init__(
        self,
        system_prompt: str | Sequence[str],
        max_tokens: int | None,
        tools: list[Tool] | None = None,
    ):
        self.model = create_model()
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens or 10_000
        self.tools = tools or []

    @property
    @abstractmethod
    def output_type(self) -> type[_DataT]: ...

    def create_agent(self):
        return Agent(
            model=self.model,
            output_type=AgentResponse[self.output_type, str],
            system_prompt=self.system_prompt,
            model_settings=ModelSettings(max_tokens=self.max_tokens),
            tools=self.tools,
        )

    def run(self, prompt: str, usage: bool = False):
        agent = self.create_agent()

        result = agent.run_sync(user_prompt=prompt)
        if usage:
            result_usage = result.usage()
            rich.print(f"[light_sea_green] Request: {result_usage}")
        return result.output
