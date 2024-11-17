import uuid
import asyncpg
from wandern.config import Config
from wandern.sql import init_migration_table

class MigrationService:
    def __init__(self, config: Config):
        self.config = config

    def generate_revision_id(self, prev_id: str | None):
        if self.config["integer_version"]:
            rev_id_int = int(prev_id) + 1 if prev_id else 1

            return "{0:04d}".format(rev_id_int)

        else:
            return uuid.uuid4().hex[-12:]

    def migration_init(self):
        # make the table in db
        # asyncpg.connect()



    def generate_revision_up(self, prev_id: str | None):
        # TODO
        revision_id = self.generate_revision_id(prev_id)
        return None
