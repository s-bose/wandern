from wandern.service import MigrationService
from wandern.models import Config


# @pytest.mark.asyncio
async def test_select(postgresql_config: dict):
    service = MigrationService(
        Config(
            dialect="postgresql",
            host=postgresql_config["host"],
            port=postgresql_config["port"],
            database=postgresql_config["database"],
            username=postgresql_config["username"],
            password=postgresql_config["password"],
            sslmode="disable",
            file_template="{version}_{description}.sql",
            integer_version=True,
        )
    )

    # await service.init_migration_table()
