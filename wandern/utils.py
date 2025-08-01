from string import Formatter
from datetime import datetime, UTC
import hashlib
import base64
from wandern.config import FileTemplateArgs


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
    prefix: str | None = None,
    author: str | None = None,
):
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
            f"Missing required fields in format string: {', '.join([f for f in missing_fields if f])}"
        ) from exc
