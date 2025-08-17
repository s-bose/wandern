import os
from pathlib import Path
import networkx as nx

from wandern.exceptions import (
    DivergentbranchError,
    InvalidMigrationFile,
    CycleDetected,
)

from wandern.file import parse_sql_file


class MigrationGraph:
    def __init__(self, graph: nx.DiGraph | None = None):
        self._graph = None
        if graph:
            self._graph = graph

    @classmethod
    def build(cls, migration_dir: str):
        graph: nx.DiGraph = nx.DiGraph()

        for file in Path(migration_dir).iterdir():
            if not os.path.isfile(file) or file.suffix != ".sql":
                raise InvalidMigrationFile("Migration file must be a sql file")

            try:
                migration_sql = parse_sql_file(file_path=file)
            except ValueError as exc:
                raise InvalidMigrationFile(
                    f"Error parsing migration file: {file.name}"
                ) from exc
            else:
                graph.add_node(migration_sql["revision_id"], **migration_sql)

        for node in graph.nodes():
            node_data = graph.nodes[node]
            if node_data["down_revision_id"] is None:
                continue

            graph.add_edge(node_data["down_revision_id"], node_data["revision_id"])

        return cls(graph=graph)

    def get_last_migration(self):
        if cycle := self.get_cycles():

            cycle_str = "\n".join(
                [f"{c[0]} {'->' if c[2] == 'forward' else '<-'} {c[1]}" for c in cycle]
            )
            raise CycleDetected(cycle_str)

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
