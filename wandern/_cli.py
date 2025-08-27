import os
from pathlib import Path
from datetime import datetime

import rich
import typer
from questionary import form, select, text, password, path

from wandern.utils import create_empty_migration
from wandern.models import Config, Revision, DatabaseProviders
from wandern.migration import MigrationService
from wandern.utils import generate_revision_id, save_config
from wandern.agents.sql_agent import MigrationAgent


def init(
    config_path: str | Path, dialect: DatabaseProviders, directory: str | None = None
):
    migration_dir = directory or os.path.join(os.getcwd(), "migrations")
    migration_dir = os.path.abspath(migration_dir)
    if os.access(migration_dir, os.F_OK) and os.listdir(migration_dir):
        rich.print(f"[red]Migration directory {migration_dir} already exists![/red]")
        raise typer.Exit(code=1)

    config = Config(
        dialect=dialect,
        dsn="",
        migration_dir=migration_dir,
    )
    save_config(config, path=config_path)
    rich.print_json(config.model_dump_json(indent=4))
    rich.print(
        "[yellow]Created config with empty dsn, please edit the dsn manually.[/yellow]"
    )


def init_interactive(config_path: str | Path):
    migration_dir = path(
        "Enter the path to the migration directory:", only_directories=True
    ).ask()

    migration_dir = os.path.abspath(migration_dir)
    if os.access(migration_dir, os.F_OK) and os.listdir(migration_dir):
        rich.print(f"[red]Migration directory {migration_dir} already exists![/red]")
        raise typer.Exit(code=1)

    db_dsn = form(
        provider=select("Select the database provider:", choices=["postgresql"]),
        username=text("Enter the database username:"),
        password=password("Enter the database password:"),
        host=text("Enter the database host:", default="localhost"),
        port=text("Enter the database port:", default="5432"),
        database=text("Enter the database name:"),
    ).ask()

    dsn = f"{db_dsn['provider']}://{db_dsn['username']}:{db_dsn['password']}@{db_dsn['host']}:{db_dsn['port']}/{db_dsn['database']}"
    config = Config(
        dialect=db_dsn["provider"],
        dsn=dsn,
        migration_dir=migration_dir,
    )

    save_config(config, config_path)
    rich.print_json(config.model_dump_json(indent=4))
    rich.print(
        f"[bold][green]Initialized wandern config in {config_path}[/green][/bold]"
    )


def generate(
    config: Config,
    message: str | None,
    author: str | None,
    tags: list[str] | None,
):
    migration_service = MigrationService(config)

    last_migration = migration_service.graph.get_last_migration()
    down_revision_id = last_migration.revision_id if last_migration else None

    revision = create_empty_migration(
        message=message,
        author=author,
        down_revision_id=down_revision_id,
        tags=tags,
    )

    filename = migration_service.save_migration(revision)
    rich.print(
        f"[green]Generated migration file: {filename} for revision:[/green]"
        f" [yellow]{revision.revision_id}[/yellow]"
    )


def generate_from_prompt(
    config: Config,
    author: str | None,
    tags: list[str] | None,
):
    prompt = typer.prompt("Describe the migration")

    agent = MigrationAgent(config=config)
    migration_service = MigrationService(config)

    response = agent.generate_revision(prompt)
    if response.error:
        rich.print(f"[red]Error:[/red] {response.error}")
        raise typer.Exit(code=1)

    last_migration = migration_service.graph.get_last_migration()
    down_revision_id = last_migration.revision_id if last_migration else None

    revision = Revision(
        revision_id=generate_revision_id(),
        down_revision_id=down_revision_id,
        up_sql=response.data.up_sql,
        down_sql=response.data.down_sql,
        message=response.data.message or "",
        tags=tags,
        author=author or "agent",
        created_at=datetime.now(),
    )

    filename = migration_service.save_migration(revision)
    rich.print(
        f"[green]Generated migration file: {filename} for revision:[/green]"
        f" [yellow]{revision.revision_id}[/yellow]"
    )

    rich.print(
        "[yellow bold]Note: This migration was generated automatically."
        " Please review and edit the migration script as necessary.[/yellow bold]"
    )
