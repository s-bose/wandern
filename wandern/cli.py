from typing import Annotated
import json
import os
import typer
import rich
from pathlib import Path
from wandern.agents.sql_agent import MigrationAgent

from wandern.constants import DEFAULT_CONFIG_FILENAME
from wandern.models import Config
from wandern.utils import load_config
from wandern.migration import MigrationService
from wandern import commands

app = typer.Typer(rich_markup_mode="rich")
config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME


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
        typer.Option(help="Optional author of the migration (default: system user)"),
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
    migration_service = MigrationService(config)

    last_migration = migration_service.graph.get_last_migration()
    down_revision_id = last_migration.revision_id if last_migration else None

    past_revisions = list(migration_service.graph.iter())

    if prompt:
        agent = MigrationAgent(
            down_revision_id=down_revision_id, past_revisions=past_revisions
        )
        prompt_text = typer.prompt("Describe the migration")
        show_usage = typer.confirm("Show usage", prompt_suffix="?")

        response = agent.run(prompt_text, usage=show_usage)
        if response.error:
            rich.print(f"[red]Error:[/red] {response.error}")
            raise typer.Exit(code=1)

        # revision = response.data

        rich.print(f"> [green][italic]{response.message}[/italic][/green]")

    else:
        revision = migration_service.create_empty_migration(
            message=message, author=author, down_revision_id=down_revision_id
        )

    # filename = migration_service.save_migration(revision)
    # rich.print(
    #     f"[green]Generated migration file: {filename} for revision:[/green]"
    #     f" [yellow]{revision.revision_id}[/yellow]"
    # )


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
def view():
    """View the currently applied migrations in db"""

    config = load_config(config_path)

    migration_service = MigrationService(config)
    migration_service.list_migrations()


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


@app.command()
def tree():
    """Visualize migration sequence as a tree"""

    config = load_config(config_path)
    migration_service = MigrationService(config)
    migration_service.list_migrations()


# @app.command()
# def prompt():
#     agent = MigrationAgent()
#     prompt = questionary.text("Prompt:").ask()
#     rich.print(f"Prompt: {prompt}")
#     response = agent.run(prompt)  # type: ignore

#     if response.error:
#         rich.print(f"[red]Error:[/red] {response.error}")
#         return

#     migration_data = response.data

#     data = generate_template(
#         template_filename="migration.sql.j2",
#         revision=migration_data,
#     )

#     with open("generated_migration.sql", "w") as f:
#         f.write(data)


@app.command()
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


@app.command()
def table():
    """Alias for 'browse' command - interactive migrations browser."""
    config = load_config(config_path)
    service = MigrationService(config)
    service.interactive_migrations_browser()
