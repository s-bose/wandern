from pathlib import Path
from datetime import datetime, UTC

from wandern.constants import MIGRATION_INIT


def normalize_name(name: str) -> str:
    return name.casefold().replace("-", "_")


def generate_script(
    revision_id: str,
    revises: str | None,
    description: str | None,
    migration_dir: str,
    fmt_timestamp: str,
    fmt_filename: str,
):
    try:
        filename = fmt_filename.format(
            revision_id=revision_id,
            description=description,
        )

        Path(migration_dir).mkdir(parents=True, exist_ok=True)

        with open(Path(migration_dir) / filename, "w") as f:
            file_content = MIGRATION_INIT.format(
                timestamp=datetime.now(tz=UTC).strftime(fmt_timestamp),
                revision_id=revision_id,
                revises=revises,
                description=description,
            )

            f.write(file_content)

    except Exception as exc:
        print(f"error generating migration script: {exc}")
        raise exc
