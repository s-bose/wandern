import pytest
import os


@pytest.fixture(scope="function")
def postgresql_config():
    return {
        "host": os.getenv("TEST_POSTGRES_HOST", "localhost"),
        "port": os.getenv("TEST_POSTGRES_PORT", "5433"),
        "username": os.getenv("TEST_POSTGRES_USER", "postgres"),
        "password": os.getenv("TEST_POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("TEST_POSTGRES_DB", "postgres"),
    }
