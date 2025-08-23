from typing import Annotated, Optional
import json
import os
import questionary
import typer
import rich
from rich.tree import Tree
from rich.panel import Panel
from rich.console import Console
from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt
from datetime import datetime
from uuid import uuid4
from questionary import text
from wandern.agents.sql_agent import MigrationAgent
from wandern.templates import generate_template
from wandern.models import Revision
from wandern.agents.models import MigrationAgentResponse

from wandern.constants import DEFAULT_FILE_FORMAT, DEFAULT_CONFIG_FILENAME
from wandern.models import Config
from wandern.utils import load_config, save_config
from wandern.databases.postgresql import PostgresMigration
from wandern.migration import MigrationService
from wandern import commands

app = typer.Typer(rich_markup_mode="rich")
config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME


@app.command()
def init(
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Run the initialization in interactive mode",
        ),
    ] = False,
    directory: Annotated[
        str | None,
        typer.Argument(
            help="Path to the directory to contain the migration scripts",
        ),
    ] = None,
):
    commands.init(interactive=interactive, directory=directory)


@app.command()
def generate(
    message: Annotated[
        str | None,
        typer.Option(
            help="A brief description of the migration",
        ),
    ] = None,
    author: Annotated[
        str | None,
        typer.Option(help="Optional author of the migration (default: system user)"),
    ] = None,
    prompt: Annotated[
        bool,
        typer.Option(
            "--prompt",
            "-p",
            help="Autogenerate migration based on natural language prompt",
        ),
    ] = False,
):
    config = load_config(config_path)
    migration_service = MigrationService(config)
    filename = migration_service.generate_migration(message=message, author=author)
    rich.print(f"[green]Generated file:[/green] [yellow]{filename}[/yellow]")


@app.command()
def upgrade(
    steps: Annotated[
        int | None,
        typer.Option(
            help="Number of migration steps to apply (default: all)",
        ),
    ] = None,
):
    config_dir = os.path.abspath(".wd.json")
    if not os.access(config_dir, os.F_OK):
        rich.print("[red]No wandern config found in the current directory[/red]")
        raise typer.Exit(code=1)

    with open(config_dir) as file:
        config = Config(**json.load(file))

    migration_service = MigrationService(config)
    migration_service.upgrade(steps=steps)


@app.command()
def downgrade(
    steps: Annotated[
        int | None,
        typer.Option(
            help="Number of migration steps to apply (default: all)",
        ),
    ] = None,
):
    config_dir = os.path.abspath(".wd.json")
    if not os.access(config_dir, os.F_OK):
        rich.print("[red]No wandern config found in the current directory[/red]")
        raise typer.Exit(code=1)

    with open(config_dir) as file:
        config = Config(**json.load(file))

    migration_service = MigrationService(config)
    migration_service.downgrade(steps=steps)


@app.command()
def view():
    """View the currently applied migrations in db"""

    config = load_config(config_path)

    migration_service = MigrationService(config)
    migration_service.list_migrations()


@app.command()
def reset():
    """Reset all migrations.
    Rolls back all the migrations till now
    """

    pass


@app.command()
def deinit():
    """Removes the migration dir and migration table.
    DOES NOT undo the migrations. Use `reset` for that.
    """
    pass


@app.command()
def tree():
    """Visualize migration sequence as a tree"""

    config = load_config(config_path)
    migration_service = MigrationService(config)
    migration_service.list_migrations()


@app.command()
def prompt():
    agent = MigrationAgent()
    prompt = questionary.text("Prompt:").ask()
    rich.print(f"Prompt: {prompt}")
    response: MigrationAgentResponse = agent.run(prompt)  # type: ignore

    if response.error:
        rich.print(f"[red]Error:[/red] {response.error}")
        return

    migration_data = response.data

    data = generate_template(
        template_filename="migration.sql.j2",
        revision=migration_data,
    )

    with open("generated_migration.sql", "w") as f:
        f.write(data)
