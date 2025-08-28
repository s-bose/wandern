from datetime import datetime
from rich.table import Table


from wandern.models import Revision


def date_validator(date_str: str):
    try:
        return bool(datetime.strptime(date_str, "%Y-%m-%d"))
    except ValueError:
        return False


def create_migration_table(revisions: list[Revision]):
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
    head_id = f"[bright_magenta]★[/bright_magenta] " f"{head_revision.revision_id[:8]}"
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
