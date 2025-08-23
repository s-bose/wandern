from functools import lru_cache
from pathlib import Path

from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment

from wandern.models import Revision


@lru_cache
def get_environment():
    template_dir = Path(__file__).parent
    loader = FileSystemLoader(template_dir)
    return SandboxedEnvironment(loader=loader)


def generate_template(template_filename: str, revision: Revision):
    env = get_environment()
    template = env.get_template(template_filename)

    return template.render(**revision.model_dump())
