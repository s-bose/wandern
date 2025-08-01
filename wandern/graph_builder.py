import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import networkx as nx

from wandern.exceptions import (
    DivergentbranchError,
    InvalidMigrationFile,
    CycleDetected,
    GraphErrror,
)

from wandern.constants import REGEX_REVISION_ID


# @dataclass
# class MigrationNode:
#     version: str
#     timestamp: datetime
#     revises: str | None = None
#     message: str | None = None
#     author: str | None = None
#     tags: list[str] | None = None

#     def __post_init__(self):
#         if self.revises == "None":
#             self.revises = None
#         if isinstance(self.timestamp, str):
#             self.timestamp = datetime.fromisoformat(self.timestamp)

#         if self.tags and isinstance(self.tags, str):
#             self.tags = [t.strip() for t in self.tags.split(",")]

#     def __hash__(self) -> int:
#         return hash(self.version)


class MigrationGraph:
    def __init__(self, graph: nx.DiGraph | None = None):
        self._graph = None
        if graph:
            self._graph = graph

    @classmethod
    def build(cls, migration_dir: str):
        graph: nx.DiGraph = nx.DiGraph()

        # revision_id, down_revision_id = None, None
        for file in Path(migration_dir).iterdir():
            if not os.path.isfile(file) or file.suffix != ".sql":
                raise InvalidMigrationFile("Migration file must be a sql file")

            with open(file, "r") as f:
                content = f.read()

                match = REGEX_REVISION_ID.search(content)
                if not match:
                    raise InvalidMigrationFile("Missing revision id")

                match_fields = match.groups()
                revision_id, down_revision_id = match_fields

                if down_revision_id == "None":
                    continue

                graph.add_edge(down_revision_id, revision_id)

        return cls(graph=graph)

    def get_last_migration(self):
        if cycle := self.get_cycles():
            raise CycleDetected(cycle)

        leaf_node = None
        if not self._graph:
            return None
        for node in self._graph.nodes():
            out_edges = self._graph.out_edges(node)

            if len(out_edges) > 1:
                to_nodes = [n[1] for n in out_edges]
                raise DivergentbranchError(
                    f"Divergent branch detected from {node} to ({', '.join(to_nodes)})"
                )

            if len(out_edges) == 0:
                leaf_node = node

        return leaf_node

    def get_cycles(self):
        try:
            cycle = nx.find_cycle(self._graph, orientation="original")
            return cycle
        except nx.NetworkXNoCycle:
            return None
