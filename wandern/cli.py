from typing import Annotated

import typer


app = typer.Typer(rich_markup_mode="rich")


@app.command()
def init(
    directory: Annotated[
        str,
        typer.Argument(
            help="Path to the directory to contain the migration scripts",
            default="migrations",
        ),
    ],
):
    """Initialize wandern for your project by providing a path to the
    migration directory.

    Wandern will create a .wandern.json config file in the directory,
    along with additional migration scripts that you will generate.
    """

    pass


@app.command()
def generate(
    message: Annotated[
        str | None,
        typer.Option(
            help="A brief description of the migration",
            default="DEFAULT_MIGRATION_MESSAGE_TIMESTAMP",
        ),
    ] = None
):
    pass
