from typing import Annotated, Optional
import json
import os
import typer
import rich
from datetime import datetime
from uuid import uuid4
from wandern.constants import TEMPLATE_DEFAULT_FILENAME
from wandern.config import Config
from wandern.utils import generate_migration_filename
from wandern.templates import generate_template
from wandern.graph_builder import DAGBuilder

from wandern.databases.postgresql import PostgresMigrationService
from wandern import commands

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
def generate(
    message: Annotated[
        str | None,
        typer.Option(
            help="A brief description of the migration",
        ),
    ] = None,
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
    revision_id, down_revision_id = builder.build()
    print(f"{revision_id=}: {down_revision_id=}")

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
                "author": None,
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
                "author": None,
            },
        )

    print(migration_body)

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

    db = PostgresMigrationService


@app.command()
def ping():
    """
    Ping database to check status and currently active migration
    """

    config_dir = os.path.abspath(".wd.json")
    if not os.access(config_dir, os.F_OK):
        rich.print("[red]No wandern config found in the current directory[/red]")
        raise typer.Exit(code=1)

    with open(config_dir) as file:
        config = Config(**json.load(file))

    db = PostgresMigrationService(config)
    result = db.get_head_revision()
    if not result:
        rich.print("[red]No migrations found in the database[/red]")
        raise typer.Exit(code=1)
    rich.print(
        f"Current head: [green]{result['id']}[/green] - revises [yellow]{result['down_revision']}[/yellow]"
        f" Created at: {result['created_at']}"
    )


@app.command()
def deinit():
    """Removes the migration dir and migration table.
    DOES NOT undo the migrations. Use `reset` for that.
    """

    pass


@app.command()
def graph(
    directory: Annotated[
        Optional[str],
        typer.Option(
            "--directory", "-d", help="Override migration directory from config"
        ),
    ] = None,
    summary: Annotated[
        bool,
        typer.Option("--summary", "-s", help="Show graph statistics and health check"),
    ] = False,
):
    """Display a visual diagram of the migration dependency graph.

    Shows the relationships between migration files as an ASCII tree diagram,
    helping you understand the migration execution order and dependencies.
    """

    # Load configuration
    config_path = os.path.abspath(".wd.json")
    if not os.access(config_path, os.F_OK):
        rich.print("[red]No wandern config found in the current directory[/red]")
        rich.print(
            "Run [bold]wandern init[/bold] to initialize wandern for this project."
        )
        raise typer.Exit(code=1)

    with open(config_path) as file:
        config_data = json.load(file)
        # Filter out unknown fields that might exist in the config file
        valid_fields = {"dialect", "dsn", "file_format", "migration_dir"}
        filtered_config = {k: v for k, v in config_data.items() if k in valid_fields}
        config = Config(**filtered_config)

    # Determine migration directory
    migration_dir = directory or config.migration_dir
    if not migration_dir:
        rich.print("[red]No migration directory specified[/red]")
        rich.print(
            "Either specify --directory or ensure migration_dir is set in .wd.json"
        )
        raise typer.Exit(code=1)

    migration_dir = os.path.abspath(migration_dir)
    if not os.access(migration_dir, os.F_OK):
        rich.print(f"[red]Migration directory does not exist: {migration_dir}[/red]")
        raise typer.Exit(code=1)

    if not os.access(migration_dir, os.R_OK):
        rich.print(f"[red]Migration directory is not readable: {migration_dir}[/red]")
        raise typer.Exit(code=1)

    # Check if directory has migration files
    migration_files = [f for f in os.listdir(migration_dir) if f.endswith(".sql")]
    if not migration_files:
        rich.print(f"[yellow]No migration files found in {migration_dir}[/yellow]")
        rich.print("Use [bold]wandern generate[/bold] to create your first migration.")
        return

    # Build and display the graph
    try:
        builder = DAGBuilder(migration_dir)
        builder.iterate()

        if summary:
            # Show just the summary statistics
            rich.print("\n[bold]Migration Graph Summary[/bold]")
            rich.print(f"Migration directory: {migration_dir}")
            rich.print(f"Total migrations: {len(builder.graph.nodes)}")
            rich.print(f"Migration connections: {len(builder.graph.edges)}")

            # Check for cycles
            cycles = builder.get_cycles()
            if cycles:
                rich.print(f"[red]⚠️  Cycles detected: {cycles}[/red]")
            else:
                rich.print("[green]✅ No cycles detected[/green]")

            # Show isolated nodes (if any)
            import networkx as nx

            isolated = list(nx.isolates(builder.graph))
            if isolated:
                rich.print(f"[yellow]⚠️  Isolated migrations: {isolated}[/yellow]")
        else:
            # Show the full ASCII graph
            rich.print("\n[bold]Migration Dependency Graph[/bold]")
            rich.print(f"Directory: {migration_dir}")
            builder.show_ascii_graph()

    except ValueError as e:
        rich.print(f"[red]Error reading migration files: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        rich.print(f"[red]Error building migration graph: {e}[/red]")
        raise typer.Exit(code=1)
