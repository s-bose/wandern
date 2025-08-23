from typing import Sequence
import uuid
from dotenv import load_dotenv

from pydantic_ai.tools import Tool
from wandern.agents.base_agent import AgentResponse
from wandern.models import Revision
from wandern.graph import MigrationGraph
from .base_agent import BaseAgent
from .models import MigrationAgentResponse

load_dotenv()


def generate_revision_id():
    return uuid.uuid4().hex[:8]


SYSTEM_PROMPT = """
You are a helpful assistant who helps users generate SQL queries based on their requests.
You have access to the following tools:

1. `generate_revision_id()` - Generates a unique 8 character revision ID for the migration file

You are tasked with generating the necessary components for a SQL migration file as per the user prompt.
The output of the request will be of type `AgentResponse` where the following schema is used:

```json
class Revision(BaseModel):
    revision_id: str
    down_revision_id: str | None
    message: str
    tags: list[str] | None = []
    author: str | None = None
    up_sql: str | None
    down_sql: str | None

class MigrationAgentResponse:
    data: Revision
    message: str
    error: str | None = None
```

The fields are defined as follows:

1. `data` - Contains the revision details you generated
    1. `revision_id`: A unique identifier for the migration revision.
    2. `down_revision_id`: The identifier of the previous migration revision.
        It will be empty if this is the first migration.
    3. `message`: A brief description of the migration.
    4. `author`: The name of the person who created the migration, if known.
    5. `tags`: A list of tags associated with the migration.
    6. `up_sql`: The SQL statements to apply the migration.
    7. `down_sql`: The SQL statements to revert the migration.
2. `message`: A brief message by the agent to the user.
3. `error`: An error message, if applicable.


You are to generate ONLY the output of the request in the format of `Revision`
and nothing more.
you need to provide a helpful message in the `message` property outlining the changes
you made to the user.
Format the SQL strings so that they are properly indented and newlined.

If you need to refer to previous migrations, you can use the `PAST REVISIONS` context
from the `ADDITIONAL CONTEXT` provided in the prompt.
"""


class MigrationAgent(BaseAgent[Revision, str]):
    def __init__(
        self,
        max_tokens: int | None = None,
        down_revision_id: str | None = None,
        past_revisions: list[Revision] = [],
    ):
        super().__init__(
            system_prompt=SYSTEM_PROMPT,
            max_tokens=max_tokens,
            tools=[Tool(function=generate_revision_id, name="generate_revision_id")],
        )

        self.down_revision_id = down_revision_id
        self.past_revisions = past_revisions

    @property
    def output_type(self):
        return Revision

    def create_structured_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        down_revision_id: str | None,
        past_revisions: list[Revision] = [],
    ):
        sanitized_prompt = f"""
        SYSTEM PROMPT
        -------------
        {system_prompt}

        USER PROMPT
        -----------
        {user_prompt}

        ADDITIONAL_CONTEXT
        ------------------
        down_revision_id = {down_revision_id}
        """

        sanitized_prompt += """PAST REVISIONS\n------------\n"""
        for rev in past_revisions:
            sanitized_prompt += f"""
            revision_id = {rev.revision_id}
            down_revision_id = {rev.down_revision_id}
            message = {rev.message}
            author = {rev.author}
            tags = {rev.tags}
            up_sql = {rev.up_sql}
            down_sql = {rev.down_sql}
            """
        return sanitized_prompt

    def run(self, prompt: str, usage: bool = False) -> AgentResponse[Revision, str]:
        custom_prompt = self.create_structured_prompt(
            SYSTEM_PROMPT,
            prompt,
            self.down_revision_id,
            past_revisions=self.past_revisions,
        )
        return super().run(
            custom_prompt,
            usage,
        )
