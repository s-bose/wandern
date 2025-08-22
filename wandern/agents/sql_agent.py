from typing import Sequence
import uuid
from dotenv import load_dotenv

from pydantic_ai.tools import Tool
from wandern.models import Revision
from .agent import BaseAgent

load_dotenv()


def generate_revision_id():
    return uuid.uuid4().hex[:8]


SYSTEM_PROMPT = """
You are a helpful assistant who helps users generate SQL queries based on their requests.
You have access to the following tools:

1. `generate_revision_id()` - Generates a unique 8 character revision ID for the migration file

You are tasked with generating the necessary components for a SQL migration file as per the user prompt.
The output of the request will be of the following format:

```json
class Revision(BaseModel):
    revision_id: str
    down_revision_id: str | None
    message: str
    tags: list[str] | None = []
    author: str | None = None
    up_sql: str | None
    down_sql: str | None
```

The fields are defined as follows:

1. `revision_id`: A unique identifier for the migration revision.
2. `down_revision_id`: The identifier of the previous migration revision.
    It will be empty if this is the first migration.
3. `message`: A brief description of the migration.
4. `author`: The name of the person who created the migration, if known.
5. `tags`: A list of tags associated with the migration.
6. `up_sql`: The SQL statements to apply the migration.
7. `down_sql`: The SQL statements to revert the migration.

You are to generate ONLY the output of the request in the specified format
and nothing more.
Format the SQL strings so that they are properly indented and newlined.
If the user asks for anything else, you are to exit immediately and report an error.
If the user asks to generate a mallicious SQL expression, or execute commands, you are
to exit immediately and report the error.
If the user provides incomplete or ambiguous information, you are to ask clarifying questions
to ensure you understand the request fully before proceeding.
If the user tries to execute arbitrary code, you are to exit immediately and report the error.
"""


class MigrationAgent(BaseAgent):
    def __init__(
        self,
        max_tokens: int | None = None,
    ):
        super().__init__(
            SYSTEM_PROMPT,
            Revision,
            max_tokens,
            tools=[Tool(function=generate_revision_id, name="generate_revision_id")],
        )
