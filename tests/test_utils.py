from wandern.utils import generate_migration_filename, slugify
from wandern.constants import DEFAULT_FILE_FORMAT
from datetime import datetime, timezone


def test_generate_migration_filename():
    # assert (
    #     generate_migration_filename(
    #         version="0001", message="test", fmt=DEFAULT_FILE_FORMAT
    #     )
    #     == f"1_{slugify('test')}_test.sql"
    # )

    current_datetime = datetime.now(timezone.utc)
    assert (
        generate_migration_filename(
            fmt="{day:02}_{month:>02}_{year}__{version}__{message}",
            version="0001",
            message="test",
        )
        == f"{current_datetime.day:02}_{current_datetime.month:02}_{current_datetime.year}__1__{'test'}.sql"
    )
