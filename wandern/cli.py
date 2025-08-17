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

# from wandern.graph_builder import DAGBuilder

from wandern.databases.postgresql import PostgresMigration
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


# @app.command()
# def generate(
#     message: Annotated[
#         str | None,
#         typer.Option(
#             help="A brief description of the migration",
#         ),
#     ] = None,
# ):
#     config_dir = os.path.abspath(".wd.json")
#     if not os.access(config_dir, os.F_OK):
#         rich.print("[red]No wandern config found in the current directory[/red]")
#         raise typer.Exit(code=1)

#     with open(config_dir) as file:
#         config = Config(**json.load(file))

#     if not config.migration_dir:
#         rich.print("[red]No migration directory specified in the config[/red]")
#         raise typer.Exit(code=1)

#     migration_dir = os.path.abspath(config.migration_dir)
#     if not os.access(migration_dir, os.W_OK):
#         rich.print("[red]Migration directory is not writeable[/red]")
#         raise typer.Exit(code=1)

#     version = uuid4().hex[:8]

#     filename = generate_migration_filename(
#         fmt=config.file_format or TEMPLATE_DEFAULT_FILENAME,
#         version=version,
#         message=message,
#     )

#     builder = DAGBuilder(migration_dir)
#     revision_id, down_revision_id = builder.build()
#     print(f"{revision_id=}: {down_revision_id=}")

#     if down_revision_id is None:
#         # first migration
#         migration_body = generate_template(
#             filename="migration.sql.j2",
#             kwargs={
#                 "timestamp": datetime.now().isoformat(),
#                 "version": version,
#                 "revises": None,
#                 "message": message,
#                 "tags": None,
#                 "author": None,
#             },
#         )

#     else:
#         migration_body = generate_template(
#             filename="migration.sql.j2",
#             kwargs={
#                 "timestamp": datetime.now().isoformat(),
#                 "version": version,
#                 "revises": revision_id,
#                 "message": message,
#                 "tags": None,
#                 "author": None,
#             },
#         )

#     print(migration_body)

#     with open(os.path.join(migration_dir, filename), "w") as file:
#         file.write(migration_body)
#         rich.print(f"[green]Created migration file {filename}[/green]")


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
