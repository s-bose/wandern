import os
from typing import Sequence
from pydantic_ai.agent import Agent
from pydantic_ai.models import Model
from pydantic_ai.tools import Tool
from pydantic_ai.settings import ModelSettings
from pydantic import BaseModel


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


SYSTEM_PROMPT = """
You are a helpful assistant that

"""


class BaseAgent:
    def __init__(
        self,
        system_prompt: str | Sequence[str],
        output_type: type[BaseModel],
        max_tokens: int | None,
        tools: list[Tool] | None = None,
    ):
        self.model = create_model()
        self.system_prompt = system_prompt
        self.output_type = output_type
        self.max_tokens = max_tokens or 10_000
        self.tools = tools or []

    def create_agent(self):
        return Agent(
            model=self.model,
            output_type=self.output_type,
            system_prompt=self.system_prompt,
            model_settings=ModelSettings(max_tokens=self.max_tokens),
            tools=self.tools,
        )

    def run(self, prompt: str) -> BaseModel:
        agent = self.create_agent()

        result = agent.run_sync(user_prompt=prompt)
        return result.output
