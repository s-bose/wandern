from typing import Annotated, Optional
from pathlib import Path
import json
import os
import typer
import rich
from datetime import datetime
from dataclasses import asdict
from uuid import uuid4

from wandern.constants import TEMPLATE_DEFAULT_FILENAME
from wandern.config import Config
from wandern.utils import generate_migration_filename
from wandern.templates.manager import generate_template
from wandern.graph_builder import DAGBuilder

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

    Wandern will create a .wd.json config file in the current directory,
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
            dsn="",
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
    if not os.access(migration_dir, os.W_OK):
        rich.print("[red]Migration directory is not writeable[/red]")
        raise typer.Exit(code=1)


    version = uuid4().hex[:8]

    filename = generate_migration_filename(
        fmt=config.file_format or TEMPLATE_DEFAULT_FILENAME,
        version=version,
        message=message,
    )

    builder = DAGBuilder(migration_dir)
    revision_id, down_revision_id = builder.iterate()

    if down_revision_id is None:
        # first migration
        migration_body = generate_template(
            filename="migration.sql.j2",
            kwargs={
                "timestamp": datetime.now().isoformat(),
                "version": version,
                "revises": None,
                "message": message,
                "tags": None,
                "author": None
            },
        )

    else:
        migration_body = generate_template(
            filename="migration.sql.j2",
            kwargs={
                "timestamp": datetime.now().isoformat(),
                "version": version,
                "revises": revision_id,
                "message": message,
                "tags": None,
                "author": None
            },
        )


    with open(os.path.join(migration_dir, filename), "w") as file:
        file.write(migration_body)
        rich.print(f"[green]Created migration file {filename}[/green]")


@app.command()
def upgrade():
    pass

@app.command()
def downgrade():
    pass

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
