from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from wandern.models import Revision


@runtime_checkable
class BaseProvider(Protocol):
    def create_table_migration(self) -> Any: ...

    def drop_table_migration(self) -> Any: ...

    def get_head_revision(self) -> Revision | None: ...

    def migrate_up(self, revision: Revision) -> Any: ...

    def migrate_down(self, revision: Revision) -> Any: ...

    def list_migrations(
        self,
        author: str | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> list[Revision]: ...
