import pytest
import os
from wandern.config import Config
from testcontainers.postgres import PostgresContainer


postgres = PostgresContainer("postgres:latest")


@pytest.fixture(scope="module", autouse=True)
def setup(request: pytest.FixtureRequest):
    postgres.start()

    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)

    os.environ["POSTGRES_USERNAME"] = postgres.username
    os.environ["POSTGRES_PASSWORD"] = postgres.password
    os.environ["POSTGRES_DB"] = postgres.dbname
    os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
    os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()


@pytest.fixture(scope="function")
def config():
    dsn = (
        f"postgresql://{os.environ['POSTGRES_USERNAME']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
        f"/{os.environ['POSTGRES_DB']}"
    )

    return Config(
        dialect="postgresql",
        dsn=dsn,
        migration_dir="migrations",
    )
