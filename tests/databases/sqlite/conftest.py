import os
import tempfile

import pytest

from wandern.models import Config


@pytest.fixture(scope="function")
def config():
    """Create a temporary SQLite database file for each test function."""
    # Create a temporary file for the SQLite database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)  # Close the file descriptor, we just need the path

    dsn = f"sqlite:///{db_path}"

    config_obj = Config(
        dsn=dsn,
        migration_dir="migrations",
    )

    yield config_obj

    # Cleanup: remove the temporary database file
    try:
        os.unlink(db_path)
    except OSError:
        pass  # File might not exist or already deleted
