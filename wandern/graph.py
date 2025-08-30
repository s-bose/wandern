import os
from pathlib import Path

import networkx as nx

from wandern.exceptions import (
    CycleDetected,
    DivergentbranchError,
    InvalidMigrationFile,
)
from wandern.models import Revision
from wandern.utils import parse_sql_file_content


class MigrationGraph:
    def __init__(self, graph: nx.DiGraph):
        self._graph: nx.DiGraph = graph

    @classmethod
    def build(cls, migration_dir: str):
        graph: nx.DiGraph = nx.DiGraph()

        for file in Path(migration_dir).iterdir():
            if not os.path.isfile(file) or file.suffix != ".sql":
                raise InvalidMigrationFile("Migration file must be a sql file")

            try:
                revision = parse_sql_file_content(file_path=file)
            except ValueError as exc:
                raise InvalidMigrationFile(
                    f"Error parsing migration file: {file.name}"
                ) from exc
            else:
                graph.add_node(revision.revision_id, **revision.model_dump())

        for node in graph.nodes():
            node_data = Revision(**graph.nodes[node])
            if node_data.down_revision_id is None:
                continue

            graph.add_edge(node_data.down_revision_id, node_data.revision_id)

        return cls(graph=graph)

    def get_last_migration(self):
        MigrationGraph.check_cycles(self._graph)
        MigrationGraph.check_divergence(self._graph)

        leaf_node = None
        for node in self._graph.nodes():
            out_edges = self._graph.out_edges(node)
            if len(out_edges) == 0:
                leaf_node = node

        if leaf_node is None:
            return None
        node_data = self._graph.nodes[leaf_node]
        return Revision(**node_data)

    @staticmethod
    def check_cycles(graph: nx.DiGraph):
        try:
            cycle = nx.find_cycle(graph, orientation="original")
            cycle_str = "\n".join(
                [f"{c[0]} {'->' if c[2] == 'forward' else '<-'} {c[1]}" for c in cycle]
            )

            raise CycleDetected(cycle_str)
        except nx.NetworkXNoCycle:
            return None

    @staticmethod
    def check_divergence(graph: nx.DiGraph):
        for node in graph.nodes():
            out_edges = graph.out_edges(node)

            if len(out_edges) > 1:
                to_nodes = [n[1] for n in out_edges]
                raise DivergentbranchError(
                    f"Divergent branch detected from {node} to ({', '.join(to_nodes)})"
                )

    @property
    def first(self) -> str | None:
        for node in self._graph.nodes():
            in_edges = self._graph.in_edges(node)
            if len(in_edges) == 0:
                return node
        return None

    def iter(self):
        first_node = self.first
        if not first_node:
            return None

        yield Revision(**self._graph.nodes[first_node])

        current_node = first_node
        while current_node:
            current_node = next(self._graph.successors(current_node), None)
            if current_node:
                yield Revision(**self._graph.nodes[current_node])

    def iter_from(self, start: str):
        if start not in self._graph.nodes:
            raise ValueError(f"Revision: {start} does not exist in the graph")

        current_node = start
        while current_node:
            current_node = next(self._graph.successors(current_node), None)
            if current_node:
                yield Revision(**self._graph.nodes[current_node])

    def get_node(self, revision_id: str) -> Revision | None:
        if revision_id not in self._graph.nodes:
            return None
        return Revision(**self._graph.nodes[revision_id])
