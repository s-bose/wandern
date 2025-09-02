import sqlite3
from datetime import datetime

from wandern.databases.base import BaseProvider
from wandern.exceptions import ConnectError
from wandern.models import Config, Revision


class SQLiteProvider(BaseProvider):
    def __init__(self, config: Config):
        self.config = config

    def connect(self) -> sqlite3.Connection:
        try:
            # Parse DSN to extract file path
            # DSN format: "sqlite:///path/to/file.db" or "sqlite:///:memory:"
            if self.config.dsn.startswith("sqlite://"):
                db_path = self.config.dsn[9:]  # Remove "sqlite://" prefix
                if db_path.startswith("/"):
                    db_path = db_path[1:]  # Remove extra leading slash
            else:
                db_path = self.config.dsn

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as exc:
            raise ConnectError(
                "Failed to connect to the database"
                f"\nIs your database server running on '{self.config.dsn}'?"
            ) from exc

    def create_table_migration(self) -> None:
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.config.migration_table} (
            revision_id TEXT PRIMARY KEY NOT NULL,
            down_revision_id TEXT,
            message TEXT,
            tags TEXT,
            author TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        with self.connect() as connection:
            connection.execute(query)

    def drop_table_migration(self) -> None:
        query = f"""
        DROP TABLE IF EXISTS {self.config.migration_table}
        """

        with self.connect() as connection:
            connection.execute(query)

    def get_head_revision(self) -> Revision | None:
        query = f"""
        SELECT * FROM {self.config.migration_table}
        ORDER BY created_at DESC LIMIT 1
        """

        with self.connect() as connection:
            result = connection.execute(query)
            row = result.fetchone()
            if not row:
                return None

            # Convert tags from TEXT to list
            tags = row["tags"].split(",") if row["tags"] else []

            return Revision(
                revision_id=row["revision_id"],
                down_revision_id=row["down_revision_id"],
                message=row["message"] or "",
                tags=tags,
                author=row["author"],
                created_at=(
                    datetime.fromisoformat(row["created_at"])
                    if row["created_at"]
                    else datetime.now()
                ),
            )

    def migrate_up(self, revision: Revision) -> int:
        query = f"""
        INSERT INTO {self.config.migration_table}
            (revision_id, down_revision_id, message, tags, author, created_at)
        VALUES (:revision_id, :down_revision_id, :message, :tags, :author, :created_at)
        """

        with self.connect() as connection:
            if revision.up_sql:
                connection.execute(revision.up_sql)

            cursor = connection.execute(
                query,
                {
                    "revision_id": revision.revision_id,
                    "down_revision_id": revision.down_revision_id,
                    "message": revision.message,
                    "tags": ",".join(revision.tags) if revision.tags else None,
                    "author": revision.author,
                    "created_at": datetime.now().isoformat(),
                },
            )

            return cursor.rowcount

    def migrate_down(self, revision: Revision) -> int:
        query = f"""
        DELETE FROM {self.config.migration_table}
        WHERE revision_id = :revision_id
        """

        with self.connect() as connection:
            if revision.down_sql:
                connection.execute(revision.down_sql)

            cursor = connection.execute(query, {"revision_id": revision.revision_id})

            return cursor.rowcount

    def list_migrations(
        self,
        author: str | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> list[Revision]:
        base_query = f"""
        SELECT * FROM {self.config.migration_table}
        """

        where_clause = []
        params = {}

        if author:
            where_clause.append("author = :author")
            params["author"] = author
        if tags:
            # For SQLite, we stored tags as comma-separated string
            # Check if any of the requested tags are in the stored tags
            tag_conditions = []
            for i, tag in enumerate(tags):
                tag_param = f"tag_{i}"
                tag_conditions.append(
                    f"(tags IS NOT NULL AND (tags = :{tag_param} OR tags LIKE :{tag_param}_prefix OR tags LIKE :_suffix_{tag_param} OR tags LIKE :_middle_{tag_param}))"
                )
                params[tag_param] = tag
                params[f"{tag_param}_prefix"] = f"{tag},%"
                params[f"_suffix_{tag_param}"] = f"%,{tag}"
                params[f"_middle_{tag_param}"] = f"%,{tag},%"
            if tag_conditions:
                where_clause.append(f"({' OR '.join(tag_conditions)})")
        if created_at:
            where_clause.append("created_at >= :created_at")
            params["created_at"] = created_at.isoformat()

        if where_clause:
            base_query += f" WHERE {' AND '.join(where_clause)}"
        base_query += " ORDER BY created_at DESC"

        with self.connect() as connection:
            result = connection.execute(base_query, params)
            rows = result.fetchall()

            revisions = []
            for row in rows:
                # Convert tags from TEXT to list
                tags_list = row["tags"].split(",") if row["tags"] else []

                revisions.append(
                    Revision(
                        revision_id=row["revision_id"],
                        down_revision_id=row["down_revision_id"],
                        message=row["message"] or "",
                        tags=tags_list,
                        author=row["author"],
                        created_at=(
                            datetime.fromisoformat(row["created_at"])
                            if row["created_at"]
                            else datetime.now()
                        ),
                    )
                )

            return revisions
