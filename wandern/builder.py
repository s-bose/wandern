import abc
from dataclasses import dataclass
from datetime import datetime
from wandern.constants import MIGRATION_INIT


@dataclass
class TemplateBuilderBase(abc.ABC):

    @abc.abstractmethod
    def build(self):
        raise NotImplementedError


class MigrationContentBuilder(TemplateBuilderBase):
    timestamp: datetime
    revision_id: str
    revises: str | None
    description: str | None

    def build(self, template_str: str = MIGRATION_INIT):
        return template_str.format(
            timestamp=self.timestamp,
            revision_id=self.revision_id,
            revises=self.revises,
            description=self.description,
        )


class MigrationFileBuilder(TemplateBuilderBase):
    timestamp: datetime
    version: str
    description: str | None

    def build(self, template_str: str = DEFAULT_FILE_TEMPLATE):
        template_str = ""
        template_str += self.version
        return template_str.format(
            version=self.version,
            description=self.description,
            timestamp=self.timestamp,
        )
