from typing import Annotated
from pathlib import Path
import os
import typer
import rich
import getpass

from wandern import _cli as commands
from wandern.constants import DEFAULT_CONFIG_FILENAME
from wandern.models import DatabaseProviders
from wandern.utils import load_config
from wandern.migration import MigrationService

app = typer.Typer(rich_markup_mode="rich")
config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME


@app.command(help="Initialize wandern for a new project")
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
    dialect: Annotated[
        DatabaseProviders,
        typer.Option(
            "--dialect",
            "-d",
            help="Database dialect to use",
        ),
    ] = DatabaseProviders.POSTGRESQL,
):
    if os.access(config_path, os.F_OK):
        rich.print("[red]Wandern config already exists in the current directory[/red]")
        raise typer.Exit(code=1)

    if interactive:
        commands.init_interactive(config_path)
    else:
        commands.init(config_path, dialect, directory)


@app.command(name="generate", help="Generate a new migration")
def generate_migration(
    message: Annotated[
        str | None,
        typer.Option(
            "--message",
            "-m",
            help="A brief description of the migration",
        ),
    ] = None,
    author: Annotated[
        str | None,
        typer.Option(
            "--author",
            "-a",
            help="Optional author of the migration (default: system user)",
        ),
    ] = None,
    tags: Annotated[
        str | None,
        typer.Option(
            "--tags",
            "-t",
            help="Comma-separated list of tags for the migration",
        ),
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
    tags_list = tags.split(", ") if tags else []
    if author is None:
        author = getpass.getuser()  # get system username

    if not prompt:
        commands.generate(config=config, message=message, author=author, tags=tags_list)
    else:
        commands.generate_from_prompt(config=config, author=author, tags=tags_list)


@app.command(help="Upgrade database migrations")
def upgrade(
    steps: Annotated[
        int | None,
        typer.Option(
            help="Number of migration steps to apply (default: all)",
        ),
    ] = None,
    tags: Annotated[
        str | None,
        typer.Option(
            "--tags",
            "-t",
            help="Comma-separated list of tags for the migration",
        ),
    ] = None,
    author: Annotated[
        str | None,
        typer.Option(
            "--author",
            "-a",
            help="Optional author of the migration",
        ),
    ] = None,
):
    config = load_config(config_path)
    tags_list = tags.split(", ") if tags else []

    migration_service = MigrationService(config)
    migration_service.upgrade(steps=steps)


@app.command(help="Downgrade database migrations")
def downgrade(
    steps: Annotated[
        int | None,
        typer.Option(
            help="Number of migration steps to apply (default: all)",
        ),
    ] = None,
):
    config = load_config(config_path)

    migration_service = MigrationService(config)
    migration_service.downgrade(steps=steps)


@app.command(help="Reset all migrations")
def reset():
    """Reset all migrations.
    Rolls back all the migrations applied to the database
    """

    config = load_config(config_path)

    migration_service = MigrationService(config)
    migration_service.downgrade(steps=None)
    rich.print("[green]Reset all migrations successfully![/green]")


@app.command(help="Browse database migrations interactively")
def browse():
    """Interactive browser for migrations with search and filtering.

    Allows you to:
    - Search migrations by text (revision ID, message, author, tags)
    - Filter by author
    - Filter by one or more tags
    - Filter by creation date
    - View migrations in a live, interactive table
    """
    config = load_config(config_path)
    service = MigrationService(config)
    service.interactive_migrations_browser()
