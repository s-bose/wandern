from typing import Annotated
from pathlib import Path
import os
import typer
import rich
import getpass
from datetime import datetime
from rich.console import Console
from questionary import form, text, password, path, select, checkbox

from wandern.agents.sql_agent import MigrationAgent
from wandern.constants import DEFAULT_CONFIG_FILENAME
from wandern.utils import (
    load_config,
    save_config,
    create_empty_migration,
)
from wandern.models import Config, DatabaseProviders
from wandern.migration import MigrationService

from wandern.cli.utils import date_validator, display_migrations_state

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
):
    if os.access(config_path, os.F_OK):
        rich.print("[red]Wandern config already exists in the current directory[/red]")
        raise typer.Exit(code=1)

    if interactive:
        migration_dir = path(
            "Enter the path to the migration directory:", only_directories=True
        ).ask()

        if not migration_dir:
            raise typer.Exit(code=1)

        migration_dir = os.path.abspath(migration_dir)
        if os.access(migration_dir, os.F_OK) and os.listdir(migration_dir):
            rich.print(
                f"[red]Migration directory {migration_dir} already exists![/red]"
            )
            raise typer.Exit(code=1)

        db_dsn = form(
            provider=select(
                "Select the database provider:",
                choices=[provider.value for provider in DatabaseProviders],
            ),
            username=text("Enter the database username:"),
            password=password("Enter the database password:"),
            host=text("Enter the database host:", default="localhost"),
            port=text("Enter the database port:", default="5432"),
            database=text("Enter the database name:"),
        ).ask()

        if not db_dsn:
            raise typer.Exit(code=1)

        dsn = (
            f"{db_dsn['provider']}://{db_dsn['username']}:{db_dsn['password']}"
            f"@{db_dsn['host']}:{db_dsn['port']}/{db_dsn['database']}"
        )
        config = Config(
            dsn=dsn,
            migration_dir=migration_dir,
        )

        save_config(config, config_path)
        rich.print_json(config.model_dump_json(indent=4))
        rich.print(
            f"[bold][green]Initialized wandern config in {config_path}[/green][/bold]"
        )

    else:
        migration_dir = directory or os.path.join(os.getcwd(), "migrations")
        migration_dir = os.path.abspath(migration_dir)
        if os.access(migration_dir, os.F_OK) and os.listdir(migration_dir):
            rich.print(
                f"[red]Migration directory {migration_dir} already exists![/red]"
            )
            raise typer.Exit(code=1)

        config = Config(
            dsn="",
            migration_dir=migration_dir,
        )
        save_config(config, path=config_path)
        rich.print_json(config.model_dump_json(indent=4))
        rich.print(
            "[yellow]Created config with empty dsn, please edit the dsn manually.[/yellow]"
        )


@app.command(name="generate", help="Generate a new migration")
def generate(
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

    migration_service = MigrationService(config)
    last_migration = migration_service.graph.get_last_migration()
    down_revision_id = last_migration.revision_id if last_migration else None

    revision = create_empty_migration(
        message=message,
        author=author,
        down_revision_id=down_revision_id,
        tags=tags_list,
    )

    if not prompt:
        filename = migration_service.save_migration(revision)
        rich.print(
            f"[green]Generated migration file: {filename} for revision:[/green]"
            f" [yellow]{revision.revision_id}[/yellow]"
        )
    else:
        user_prompt = typer.prompt("Describe the migration")
        agent = MigrationAgent(config=config)
        response = agent.generate_revision(user_prompt)
        if response.error:
            rich.print(f"[red]Error:[/red] {response.error}")
            raise typer.Exit(code=1)

        revision.message = response.data.message or ""
        revision.tags = tags_list
        revision.up_sql = response.data.up_sql
        revision.down_sql = response.data.down_sql

        filename = migration_service.save_migration(revision)
        rich.print(
            f"[green]Generated migration file: {filename} for revision:[/green]"
            f" [yellow]{revision.revision_id}[/yellow]"
        )

    rich.print(
        "[yellow bold]Note: This migration was generated automatically."
        " Please review and edit the migration script as necessary.[/yellow bold]"
    )


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
    if author:
        rich.print(f"[green]Applying migrations by author: {author}[/green]")
    if tags:
        rich.print(f"[green]Applying migrations with tags: {tags}[/green]")

    migration_service = MigrationService(config)
    migration_service.upgrade(steps=steps, author=author, tags=tags_list)


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
    """Interactive browser for migrations with search and filtering."""
    config = load_config(config_path)
    service = MigrationService(config)
    console = Console(force_terminal=True)

    all_revisions = service.database.list_migrations()
    authors = sorted(set(rev.author for rev in all_revisions if rev.author))
    tags = sorted(set(tag for rev in all_revisions for tag in rev.tags or []))

    author_filter = None
    tags_filter = []
    date_filter = None

    while True:
        filtered_revisions = service.filter_migrations(
            author=author_filter,
            tags=tags_filter if tags_filter else None,
            created_at=date_filter,
        )

        display_migrations_state(
            console, filtered_revisions, author_filter, tags_filter, date_filter
        )

        action = select(
            "Select an action:", choices=["Author", "Tags", "Date", "Clear", "Exit"]
        ).ask()

        if action == "Exit" or action is None:
            break
        elif action == "Author":
            if authors:
                selected = select("Select author:", choices=["[Clear]"] + authors).ask()
                author_filter = None if selected == "[Clear]" else selected
        elif action == "Tags":
            if tags:
                tags_filter = checkbox("Select tags:", choices=tags).ask() or []
        elif action == "Date":
            date_input = text(
                "Enter date (YYYY-MM-DD, empty to clear):", validate=date_validator
            ).ask()
            if date_input and date_input.strip():
                try:
                    date_filter = datetime.strptime(date_input.strip(), "%Y-%m-%d")
                except ValueError:
                    pass
            else:
                date_filter = None
        elif action == "Clear":
            author_filter = None
            tags_filter = []
            date_filter = None

    raise typer.Exit()
