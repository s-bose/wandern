from typing import Unpack
from string import Formatter
from pathlib import Path
from datetime import datetime, UTC
import hashlib
import base64
import uuid

from wandern.constants import MIGRATION_INIT, TEMPLATE_DEFAULT_FILENAME
from wandern.config import FileTemplateArgs, Config


def slugify(text: str, length: int = 10) -> str:
    hash_obj = hashlib.sha256(text.encode())
    hash_digest = hash_obj.digest()
    b64_str = base64.urlsafe_b64encode(hash_digest).decode("utf-8")
    slug = "".join(c for c in b64_str if c.isalnum())

    return slug if len(slug) <= length else slug[:length]


def generate_migration_filename(
    *,
    fmt: str = TEMPLATE_DEFAULT_FILENAME,
    version: str,
    message: str | None,
    prefix: str | None = None,
    author: str | None = None,
):
    current_timestamp = datetime.now(tz=UTC)
    kwargs: FileTemplateArgs = {
        "version": int(version) if version.isnumeric() else version,
        "slug": slugify(message),
        "message": message,
        "epoch": current_timestamp.timestamp(),
        "year": current_timestamp.year,
        "month": current_timestamp.month,
        "day": current_timestamp.day,
        "hour": current_timestamp.hour,
        "minute": current_timestamp.minute,
        "second": current_timestamp.second,
        "author": author,
        "prefix": prefix,
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
            f"Missing required fields in format string: {', '.join(missing_fields)}"
        ) from exc

    # try:
    #     Path(migration_dir).mkdir(parents=True, exist_ok=True)

    #     with open(Path(migration_dir) / filename, "w", encoding="utf-8") as f:
    #         file_content = MIGRATION_INIT.format(
    #             revision_id=revision_id,
    #             revises=revises,
    #             description=description,
    #         )

    #         f.write(file_content)

    # except Exception as exc:
    #     print(f"error generating migration script: {exc}")
    #     raise exc
