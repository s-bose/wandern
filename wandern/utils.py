from string import Formatter
from datetime import datetime, UTC
from pathlib import Path
import os
import json
import hashlib
import base64
import uuid
import rich
import typer
from wandern.models import FileTemplateArgs, Config
from wandern.constants import REGEX_MIGRATION_PARSER, DEFAULT_CONFIG_FILENAME
from wandern.models import Revision


def slugify(text: str, length: int = 10) -> str:
    hash_obj = hashlib.sha256(text.encode())
    hash_digest = hash_obj.digest()
    b64_str = base64.urlsafe_b64encode(hash_digest).decode("utf-8")
    slug = "".join(c for c in b64_str if c.isalnum())

    return slug if len(slug) <= length else slug[:length]


def generate_migration_filename(
    *,
    fmt: str,
    version: str,
    message: str | None,
    author: str | None = None,
) -> str:
    current_timestamp = datetime.now(tz=UTC)
    kwargs: FileTemplateArgs = {
        "version": str(int(version)) if version.isnumeric() else version,
        "slug": slugify(message) if message else "",
        "message": message.replace(" ", "_") if message else None,
        "epoch": current_timestamp.timestamp(),
        "year": str(current_timestamp.year),
        "month": str(current_timestamp.month),
        "day": str(current_timestamp.day),
        "hour": str(current_timestamp.hour),
        "minute": str(current_timestamp.minute),
        "second": str(current_timestamp.second),
        "author": author,
    }
    if not kwargs["version"] and not (kwargs["slug"] or kwargs["message"]):
        raise ValueError("version or slug or message is required")

    formatter = Formatter()
    parsed_fmt = formatter.parse(fmt)
    try:
        filename = fmt.format(**kwargs)
        return filename + ".sql" if not filename.endswith(".sql") else filename
    except KeyError as exc:
        missing_fields = [fname for _, fname, _, _ in parsed_fmt if fname not in kwargs]
        raise ValueError(
            f"Missing required fields in format string: {', '.join([f for f in missing_fields if f])}"
        ) from exc


def parse_sql_file_content(file_path: str | Path) -> Revision:
    with open(file_path, encoding="utf-8") as file:
        content = file.read()

        match = REGEX_MIGRATION_PARSER.search(content)

        if not match:
            raise ValueError("Invalid migration file format")

        group: dict[str, str] = match.groupdict()
        revision_id = group["revision_id"].strip()
        down_revision_id: str | None = group["revises"].strip()
        created_at = group["timestamp"].strip()
        message = group["message"].strip()
        author = group["author"].strip() if group["author"] else None
        tags = group["tags"].strip().split(",") if group["tags"] else None
        up_sql = group["up_sql"].strip()
        down_sql = group["down_sql"].strip()

        return Revision(
            revision_id=revision_id,
            down_revision_id=(
                None
                if not down_revision_id or down_revision_id.lower() == "none"
                else down_revision_id
            ),
            message=message,
            author=author,
            tags=tags,
            up_sql=up_sql,
            down_sql=down_sql,
            created_at=datetime.fromisoformat(created_at),
        )


def generate_revision_id() -> str:
    return uuid.uuid4().hex[:8]


def create_empty_migration(
    message: str | None,
    down_revision_id: str | None,
    author: str | None = None,
    tags: list[str] | None = None,
) -> Revision:
    version = generate_revision_id()

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


def load_config(path: str | Path) -> Config:
    config_dir = os.path.abspath(path)
    if not os.access(config_dir, os.F_OK):
        rich.print("[red]No wandern config found in the current directory[/red]")
        raise typer.Exit(1)

    with open(config_dir, encoding="utf-8") as file:
        config = Config(**json.load(file))

    migration_dir = os.path.abspath(config.migration_dir)
    if not os.access(migration_dir, os.W_OK):
        rich.print("[red]Migration directory is not writeable[/red]")
        raise typer.Exit(code=1)

    return config


def save_config(config: Config, path: str | Path) -> None:
    config_dir = os.path.abspath(path)

    with open(config_dir, "w", encoding="utf-8") as file:
        file.write(config.model_dump_json(indent=4))
