import os
import typer
import rich
import json
from questionary import form, text, select, password, path
from dataclasses import asdict
from wandern.models import Config
from wandern.utils import generate_migration_filename, load_config, save_config
from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.graph import MigrationGraph
from wandern.exceptions import CycleDetected, DivergentbranchError


def init(interactive: bool = False, directory: str | None = None):
    # config_dir = os.path.abspath(".wd.json")
    # if os.access(config_dir, os.F_OK):
    #     rich.print("[red]Wandern config already exists in the current directory[/red]")
    #     raise typer.Exit(code=1)

    if interactive:
        migration_dir = path(
            "Enter the path to the migration directory:", only_directories=True
        ).ask()

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

    else:
        migration_dir = directory or os.path.join(os.getcwd(), "migrations")
        config = Config(
            dialect="postgresql",
            dsn="",
            migration_dir=migration_dir,
        )

    migration_dir = os.path.abspath(migration_dir)
    if os.access(migration_dir, os.F_OK) and os.listdir(migration_dir):
        rich.print(f"[red]Migration directory {migration_dir} already exists![/red]")
        raise typer.Exit(code=1)

    save_config(config, config_dir)
    rich.print_json(json.dumps(asdict(config)), indent=4)
    if interactive:
        rich.print(
            f"[bold][green]Initialized wandern config in {config_dir}[/green][/bold]"
        )
    else:
        rich.print(
            "[yellow]Created config with empty dsn, please edit the dsn manually.[/yellow]"
        )
