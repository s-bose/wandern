from typing import Annotated, Optional
from pathlib import Path
import json
import os
import typer
import rich
from dataclasses import asdict

from wandern.config import Config

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def init(
    directory: Annotated[
        str,
        typer.Argument(
            help="Path to the directory to contain the migration scripts",
        ),
    ] = "migrations",
):
    """Initialize wandern for your project by providing a path to the
    migration directory.

    Wandern will create a .wandern.json config file in the current directory,
    and the directory, if specified will contain the migration scripts.
    """

    if os.access(directory, os.F_OK) and os.listdir(directory):
        rich.print(f"[red]Directory {directory} already exists and is not empty[/red]")
        raise typer.Exit(
            code=1,
        )

    migration_dir = os.path.abspath(directory)
    if not os.path.exists(migration_dir):
        Path(migration_dir).mkdir(parents=True, exist_ok=True)
        rich.print(f"[green]Created migration directory {migration_dir}[/green]")

    config_dir = os.path.abspath(".wd.json")
    with open(config_dir, "w") as cfg_file:
        config_obj = Config(
            dialect="postgresql",
            host="",
            port="",
            database="",
            username="",
            password="",
            sslmode="",
            migration_dir=directory,
        )
        json.dump(asdict(config_obj), cfg_file, indent=4)

    rich.print(
        f"[bold][green]Initialized wandern config in {config_dir}[/green][/bold]"
    )


@app.command()
def generate(
    message: Annotated[
        str,
        typer.Option(
            help="A brief description of the migration",
        ),
    ],
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
    if config.integer_version:
        version_num = None  # TODO


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
