from typing import Protocol, Any, runtime_checkable
from datetime import datetime

from wandern.types import Revision


@runtime_checkable
class DatabaseMigration(Protocol):
    def create_table_migration(self) -> Any: ...

    def drop_table_migration(self) -> Any: ...

    def get_head_revision(self) -> Any | None: ...

    def migrate_up(self, revision: Revision) -> None: ...

    def migrate_down(self, revision: Revision) -> None: ...

    def update_migration(
        self, revision_id: str, down_revision_id: str, timestamp: datetime
    ) -> Any: ...
