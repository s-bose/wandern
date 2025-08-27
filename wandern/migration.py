import rich
from rich.console import Console
from rich.table import Table
import os
from uuid import uuid4
from datetime import datetime
from wandern.models import Config, Revision

from wandern.databases.provider import get_database_impl
from wandern.graph import MigrationGraph
from wandern.utils import generate_migration_filename
from wandern.constants import DEFAULT_FILE_FORMAT
from wandern.templates.engine import generate_template


class MigrationService:
    def __init__(self, config: Config):
        self.config = config
        self.database = get_database_impl(config.dialect, config=config)
        self.graph = MigrationGraph.build(config.migration_dir)

    def upgrade(self, steps: int | None = None):
        self.database.create_table_migration()
        head = self.database.get_head_revision()
        count = 0

        if not head:
            # first migration
            for revision in self.graph.iter():
                self.database.migrate_up(revision)
                up_msg = (
                    f"(UP) [green]{revision.down_revision_id} -> "
                    f"{revision.revision_id}[/green]"
                )
                rich.print(up_msg)
                count += 1
                if steps and count == steps:
                    break
        else:
            for revision in self.graph.iter_from(head.revision_id):
                self.database.migrate_up(revision)
                rich.print(
                    f"(UP) [green]{revision.down_revision_id} -> {revision.revision_id}[/green]"
                )
                count += 1
                if steps and count == steps:
                    break

    def downgrade(self, steps: int | None = None):
        head = self.database.get_head_revision()
        if not head:
            # No migration to downgrade
            return

        current = self.graph.get_node(head.revision_id)
        if not current:
            raise ValueError(
                f"Migration file for revision {head.revision_id} not found"
            )

        count = 0
        while current and (steps is None or count < steps):
            self.database.migrate_down(current)
            if not current.down_revision_id:
                break
            rich.print(
                f"(DOWN) [red]{current.revision_id} -> {current.down_revision_id}[/red]"
            )
            current = self.graph.get_node(current.down_revision_id)
            count += 1

    def create_empty_migration(
        self,
        message: str | None,
        down_revision_id: str | None,
        author: str | None = None,
        tags: list[str] | None = None,
    ) -> Revision:
        version = uuid4().hex[:8]

        return Revision(
            revision_id=version,
            down_revision_id=down_revision_id,
            message=message or "",
            tags=tags,
            author=author,
            up_sql=None,
            down_sql=None,
            created_at=datetime.now(),
        )

    def save_migration(self, revision: Revision):
        filename = generate_migration_filename(
            fmt=self.config.file_format or DEFAULT_FILE_FORMAT,
            version=revision.revision_id,
            message=revision.message,
            author=revision.author,
        )

        migration_body = generate_template(
            template_filename="migration.sql.j2", revision=revision
        )

        migration_dir_abs = os.path.abspath(self.config.migration_dir)
        with open(
            os.path.join(migration_dir_abs, filename), "w", encoding="utf-8"
        ) as file:
            file.write(migration_body)

        return filename

    def list_migrations(self):
        revisions = self.database.list_migrations()

        table = Table(title="Migrations")

        table.add_column("Revision ID", style="cyan", no_wrap=True, justify="right")
        table.add_column("Down Revision", style="magenta", justify="right")
        table.add_column("Applied At", style="green", justify="right")

        if revisions:
            table.add_row(
                f"[bright_magenta](HEAD)[/bright_magenta] {revisions[0].revision_id}",
                f'{revisions[0].down_revision_id or "None"}',
                f'{revisions[0].created_at.strftime("%Y-%m-%d %H:%M:%S")}',
            )
            for rev in revisions[1:]:
                table.add_row(
                    rev.revision_id,
                    rev.down_revision_id or "None",
                    rev.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                )

        rich.print(table)

    def _create_migrations_table(self, revisions: list[Revision]) -> Table:
        """Create a clean table of migrations."""
        table = Table(show_header=True, header_style="bold blue")

        table.add_column("ID", style="cyan", no_wrap=True, width=10)
        table.add_column("Message", style="white", max_width=30)
        table.add_column("Author", style="yellow", width=12)
        table.add_column("Tags", style="blue", max_width=20)
        table.add_column("Date", style="green", width=12)

        if not revisions:
            table.add_row("No migrations found", "", "", "", "")
            return table

        # Add HEAD indicator for the first migration
        head_revision = revisions[0]
        head_id = (
            f"[bright_magenta]★[/bright_magenta] " f"{head_revision.revision_id[:8]}"
        )
        table.add_row(
            head_id,
            head_revision.message or "",
            head_revision.author or "",
            ", ".join(head_revision.tags or []),
            head_revision.created_at.strftime("%m-%d %H:%M"),
        )

        # Add remaining migrations
        for rev in revisions[1:]:
            table.add_row(
                rev.revision_id[:8],
                rev.message or "",
                rev.author or "",
                ", ".join(rev.tags or []),
                rev.created_at.strftime("%m-%d %H:%M"),
            )

        return table

    def _get_all_authors(self) -> list[str]:
        """Get all unique authors from migrations."""
        all_revisions = self.database.list_migrations()
        authors = list(set(rev.author for rev in all_revisions if rev.author))
        return sorted(authors)

    def _get_all_tags(self) -> list[str]:
        """Get all unique tags from migrations."""
        all_revisions = self.database.list_migrations()
        all_tags = set()
        for rev in all_revisions:
            if rev.tags:
                all_tags.update(rev.tags)
        return sorted(list(all_tags))

    def _handle_author_filter(self) -> str | None:
        """Handle author selection and return selected author."""
        import questionary

        authors = self._get_all_authors()
        if not authors:
            console = Console()
            console.print("[yellow]No authors found[/yellow]")
            return None

        choices = ["[Clear filter]"] + authors
        selected = questionary.select("Select author:", choices=choices).ask()

        if selected and selected != "[Clear filter]":
            return selected
        return None

    def _handle_tags_filter(self) -> list[str]:
        """Handle tag selection and return selected tags."""
        import questionary

        all_tags = self._get_all_tags()
        if not all_tags:
            console = Console()
            console.print("[yellow]No tags found[/yellow]")
            return []

        selected_tags = questionary.checkbox("Select tags:", choices=all_tags).ask()

        return selected_tags if selected_tags is not None else []

    def _handle_date_filter(self) -> datetime | None:
        """Handle date selection and return selected date."""
        import questionary

        date_input = questionary.text(
            "Enter date (YYYY-MM-DD) or leave empty to clear:",
            validate=lambda x: not x or (len(x) == 10 and x.count("-") == 2),
        ).ask()

        if date_input:
            try:
                return datetime.strptime(date_input, "%Y-%m-%d")
            except ValueError:
                console = Console()
                console.print("[red]Invalid date format[/red]")
        return None

    def interactive_migrations_browser(self):
        """
        Interactive migrations browser with simple select-based filtering.
        """
        import questionary

        console = Console()

        # Initialize filters
        author_filter = None
        tags_filter = []
        date_filter = None

        try:
            while True:
                # Get filtered revisions
                revisions = self.database.list_migrations(
                    author=author_filter, tags=tags_filter, created_at=date_filter
                )

                # Display current table
                console.clear()
                console.print("[bold blue]Interactive Migrations Browser[/bold blue]")
                console.print()
                console.print(self._create_migrations_table(revisions))

                # Show active filters below the table
                filter_info = []
                if author_filter:
                    filter_info.append(f"Author: {author_filter}")
                if tags_filter:
                    filter_info.append(f"Tags: {', '.join(tags_filter)}")
                if date_filter:
                    date_str = date_filter.strftime("%Y-%m-%d")
                    filter_info.append(f"Date: {date_str}")

                console.print()
                if filter_info:
                    filters_text = f"Active filters: {' | '.join(filter_info)}"
                    console.print(f"[dim]{filters_text}[/dim]")
                else:
                    console.print("[dim]No filters active[/dim]")
                console.print()

                # Main filter selection
                filter_choices = [
                    "Author",
                    "Tags",
                    "Created Date",
                    "Clear All Filters",
                    "Exit",
                ]

                selected_filter = questionary.select(
                    "Select filter type:", choices=filter_choices
                ).ask()

                if selected_filter == "Exit" or selected_filter is None:
                    break
                elif selected_filter == "Author":
                    author_filter = self._handle_author_filter()
                elif selected_filter == "Tags":
                    tags_filter = self._handle_tags_filter()
                elif selected_filter == "Created Date":
                    date_filter = self._handle_date_filter()
                elif selected_filter == "Clear All Filters":
                    author_filter = None
                    tags_filter = []
                    date_filter = None
                    console.print("[green]All filters cleared[/green]")

        except KeyboardInterrupt:
            pass
        finally:
            console.print("\n[dim]Goodbye![/dim]")
