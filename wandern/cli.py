from typing import Annotated, Optional
import json
import os
import typer
import rich
from datetime import datetime
from uuid import uuid4
from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.config import Config
from wandern.utils import generate_migration_filename
from wandern.templates import generate_template
from questionary import text

from wandern.graph import MigrationGraph

from wandern.databases.postgresql import PostgresMigration
from wandern.migration import MigrationService
from wandern import commands
from wandern.agents.sql_agent import SqlAgent

app = typer.Typer(rich_markup_mode="rich")


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
def prompt():
    agent = SqlAgent()
    prompt = text(
        "Write what you want to generate in the migration script in plain english:"
    ).ask()
    agent.run(prompt)


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
):
    config_dir = os.path.abspath(".wd.json")
    if not os.access(config_dir, os.F_OK):
        rich.print("[red]No wandern config found in the current directory[/red]")
        raise typer.Exit(code=1)

    with open(config_dir) as file:
        config = Config(**json.load(file))

    if not config.migration_dir:
        rich.print("[red]No migration directory specified in the config[/red]")
        raise typer.Exit(code=1)

    migration_dir = os.path.abspath(config.migration_dir)
    if not os.access(migration_dir, os.W_OK):
        rich.print("[red]Migration directory is not writeable[/red]")
        raise typer.Exit(code=1)

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
def reset():
    """Reset all migrations.
    Rolls back all the migrations till now
    """

    db = PostgresMigration


# @app.command()
# def ping():
#     """
#     Ping database to check status and currently active migration
#     """

#     config_dir = os.path.abspath(".wd.json")
#     if not os.access(config_dir, os.F_OK):
#         rich.print("[red]No wandern config found in the current directory[/red]")
#         raise typer.Exit(code=1)

#     with open(config_dir) as file:
#         config = Config(**json.load(file))

#     db = PostgresMigrationService(config)
#     result = db.get_head_revision()
#     if not result:
#         rich.print("[red]No migrations found in the database[/red]")
#         raise typer.Exit(code=1)
#     rich.print(
#         f"Current head: [green]{result['id']}[/green] - revises [yellow]{result['down_revision']}[/yellow]"
#         f" Created at: {result['created_at']}"
#     )


@app.command()
def deinit():
    """Removes the migration dir and migration table.
    DOES NOT undo the migrations. Use `reset` for that.
    """

    pass
