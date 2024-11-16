from typing import Annotated
import logging
import json
import os
import typer
import rich

from wandern.config import Config
from wandern.constants import DEFAULT_FILE_TEMPLATE

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def init(
    directory: Annotated[
        str,
        typer.Option(
            help="Path to the directory to contain the migration scripts",
        ),
    ] = "migrations",
):
    """Initialize wandern for your project by providing a path to the
    migration directory.

    Wandern will create a .wandern.json config file in the directory,
    along with additional migration scripts that you will generate.
    """
    if os.access(directory, os.F_OK) and os.listdir(directory):
        logging.error(
            f"Directory {directory} already exists and is not empty",
        )
        raise typer.Exit(
            code=1,
        )

    if not os.path.exists(directory):
        os.mkdir(directory)

    with open(os.path.join(directory, ".wd.json"), "w") as cfg_file:
        config_obj = Config(
            dialect="postgresql",
            host="",
            port="",
            database="",
            username="",
            password="",
            sslmode="",
            file_template=DEFAULT_FILE_TEMPLATE,
            prefer_int_version=False,
        )
        json.dump(config_obj, cfg_file, indent=4)

    rich.print(
        f"[bold][green]Initialized wandern config in {os.path.abspath(directory)}[/green][/bold]"
    )


@app.command()
def generate(
    message: Annotated[
        str,
        typer.Option(
            help="A brief description of the migration",
        ),
    ]
):
    pass
