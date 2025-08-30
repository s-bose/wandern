from functools import lru_cache
from pathlib import Path
from typing import Literal

from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment

from wandern.models import Revision

TemplateFile = Literal["migration.sql.j2"]


@lru_cache
def get_environment():
    template_dir = Path(__file__).parent
    loader = FileSystemLoader(template_dir)
    return SandboxedEnvironment(loader=loader)


def generate_template(template_filename: TemplateFile, revision: Revision):
    env = get_environment()
    template = env.get_template(template_filename)

    return template.render(**revision.model_dump())
