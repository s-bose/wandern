import os

import pytest
from testcontainers.mysql import MySqlContainer

from wandern.models import Config

mysql_container = MySqlContainer("mysql:8.0")


@pytest.fixture(scope="module", autouse=True)
def setup(request: pytest.FixtureRequest):
    mysql_container.start()

    def remove_container():
        mysql_container.stop()

    request.addfinalizer(remove_container)

    os.environ["MYSQL_USERNAME"] = mysql_container.username
    os.environ["MYSQL_PASSWORD"] = mysql_container.password
    os.environ["MYSQL_DB"] = mysql_container.dbname
    os.environ["MYSQL_PORT"] = str(mysql_container.get_exposed_port(3306))
    os.environ["MYSQL_HOST"] = mysql_container.get_container_host_ip()


@pytest.fixture(scope="function")
def config():
    dsn = (
        f"mysql://{os.environ['MYSQL_USERNAME']}:"
        f"{os.environ['MYSQL_PASSWORD']}@"
        f"{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}"
        f"/{os.environ['MYSQL_DB']}"
    )

    return Config(
        dsn=dsn,
        migration_dir="migrations",
    )
