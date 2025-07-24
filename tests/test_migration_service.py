import pytest
import os
import tempfile
from wandern.services.migration import MigrationService
from wandern.config import Config


def test_create_migration_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        migration_service = MigrationService(
            config=Config(
                dialect="postgresql",
                dsn="postgresql://postgres:postgres@localhost:5432/postgres",
                migration_dir=temp_dir,
                file_format="{version:04d}_{message}.sql",
            )
        )
        migration_service.create_migration_file(
            version="1", message="test", author="test"
        )

        assert os.path.exists(os.path.join(temp_dir, "0001_test.sql"))
