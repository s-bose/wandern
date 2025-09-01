from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wandern.models import Revision


def date_validator(date_str: str) -> bool:
    try:
        return bool(datetime.strptime(date_str, "%Y-%m-%d"))
    except ValueError:
        return False


def create_migration_table(
    revisions: list[Revision],
    sources: list[str] | None = None,
    db_head_id: str | None = None,
) -> Table:
    table = Table(show_header=True, header_style="bold blue", expand=True)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Message", style="white")
    table.add_column("Author", style="yellow")
    table.add_column("Tags", style="blue")
    table.add_column("Date", style="green")
    if sources:
        table.add_column("Status", style="bright_magenta")

    if not revisions:
        empty_row = ["No migrations found", "", "", "", ""]
        if sources:
            empty_row.append("")
        table.add_row(*empty_row)
        return table

    # Add first migration (with HEAD indicator only if it's the database HEAD)
    first_revision = revisions[0]
    is_db_head = db_head_id and first_revision.revision_id == db_head_id
    revision_id_display = (
        f"[bright_magenta]★[/bright_magenta] {first_revision.revision_id[:8]}"
        if is_db_head
        else first_revision.revision_id[:8]
    )
    first_row = [
        revision_id_display,
        first_revision.message or "",
        first_revision.author or "",
        ", ".join(first_revision.tags or []),
        first_revision.created_at.strftime("%m-%d %H:%M"),
    ]
    if sources:
        status_style = (
            "[green]Applied[/green]"
            if sources[0] == "applied"
            else "[red]Not applied[/red]"
        )
        first_row.append(status_style)
    table.add_row(*first_row)

    for i, rev in enumerate(revisions[1:], 1):
        # Check if this revision is the database HEAD
        is_db_head = db_head_id and rev.revision_id == db_head_id
        revision_id_display = (
            f"[bright_magenta]★[/bright_magenta] {rev.revision_id[:8]}"
            if is_db_head
            else rev.revision_id[:8]
        )

        row = [
            revision_id_display,
            rev.message or "",
            rev.author or "",
            ", ".join(rev.tags or []),
            rev.created_at.strftime("%m-%d %H:%M"),
        ]
        if sources:
            status_style = (
                "[green]Applied[/green]"
                if sources[i] == "applied"
                else "[red]Not applied[/red]"
            )
            row.append(status_style)
        table.add_row(*row)

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
    sources: list[str] | None = None,
    db_head_id: str | None = None,
) -> None:
    """Display the current state with table and filters"""
    console.clear()
    console.print(
        Panel(
            create_migration_table(filtered_revisions, sources, db_head_id),
            title="[bold blue]Migrations[/bold blue]",
        )
    )
    console.print(create_filter_panel(author_filter, tags_filter, date_filter))
