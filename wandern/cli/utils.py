from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from wandern.models import Revision


def date_validator(date_str: str) -> bool:
    try:
        return bool(datetime.strptime(date_str, "%Y-%m-%d"))
    except ValueError:
        return False


def create_migration_table(revisions: list[Revision]) -> Table:
    table = Table(show_header=True, header_style="bold blue")

    table.add_column("ID", style="cyan", no_wrap=True, max_width=20)
    table.add_column("Message", style="white", max_width=30)
    table.add_column("Author", style="yellow", width=12)
    table.add_column("Tags", style="blue", max_width=20)
    table.add_column("Date", style="green", width=12)

    if not revisions:
        table.add_row("No migrations found", "", "", "", "")
        return table

    # Add HEAD indicator for the first migration
    head_revision = revisions[0]
    head_id = f"[bright_magenta]★[/bright_magenta] {head_revision.revision_id[:8]}"
    table.add_row(
        head_id,
        head_revision.message or "",
        head_revision.author or "",
        ", ".join(head_revision.tags or []),
        head_revision.created_at.strftime("%m-%d %H:%M"),
    )

    for rev in revisions[1:]:
        table.add_row(
            rev.revision_id[:8],
            rev.message or "",
            rev.author or "",
            ", ".join(rev.tags or []),
            rev.created_at.strftime("%m-%d %H:%M"),
        )

    return table


def create_filter_panel(
    author_filter: str | None,
    tags_filter: list[str] | None,
    date_filter: datetime | None,
) -> Panel:
    """Create the filter information panel"""
    filter_info = []
    if author_filter:
        filter_info.append(f"[yellow]Author:[/yellow] {author_filter}")
    if tags_filter:
        filter_info.append(f"[blue]Tags:[/blue] {', '.join(tags_filter)}")
    if date_filter:
        date_str = date_filter.strftime("%Y-%m-%d")
        filter_info.append(f"[green]Date:[/green] after {date_str}")

    filter_text = (
        " | ".join(filter_info) if filter_info else "[dim]No filters active[/dim]"
    )

    return Panel(
        filter_text,
        title="[bold bright_blue]Filters[/bold bright_blue]",
        border_style="bright_blue",
    )


def display_migrations_state(
    console: Console,
    filtered_revisions: list[Revision],
    author_filter: str | None,
    tags_filter: list[str] | None,
    date_filter: datetime | None,
) -> None:
    """Display the current state with table and filters"""
    console.clear()
    console.print(
        Panel(
            create_migration_table(filtered_revisions),
            title="[bold blue]Migrations[/bold blue]",
        )
    )
    console.print(create_filter_panel(author_filter, tags_filter, date_filter))
