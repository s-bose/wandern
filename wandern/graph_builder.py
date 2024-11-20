from collections import defaultdict
from typing import Pattern
import os
import re
import networkx as nx
from matplotlib import pyplot as plt


class DAGBuilder:
    def __init__(self, migration_dir: str):
        self.migration_dir = migration_dir

        self.regex_revision_ids: Pattern = re.compile(
            r"Revision ID: (?P<revision_id>\w+)\nRevises: (?P<down_revision_id>\w+)"
        )

        self.graph = nx.DiGraph()

    def iterate(self):
        for file in os.listdir(self.migration_dir):
            if file == ".wd.json":
                continue
            file_path = os.path.join(self.migration_dir, file)
            if not os.path.isfile(file_path) or not file.endswith(".sql"):
                raise ValueError("invalid migration file, must be a sql file")

            with open(file_path, "r") as f:
                content = f.read()

                match = self.regex_revision_ids.search(content)
                if not match:
                    raise ValueError("invalid migration file, missing revision id")

                revision_id = match.group("revision_id")
                down_revision_id = match.group("down_revision_id")

                if not any([revision_id, down_revision_id]):
                    raise ValueError("invalid migration file, missing revision id")

                self.graph.add_edge(down_revision_id, revision_id)

    def show_graph(self):
        nx.draw(
            self.graph,
            nodelist=list(self.graph.nodes),
            node_size=[len(node) * 500 for node in list(self.graph.nodes)],
            with_labels=True,
            pos=nx.spring_layout(self.graph, seed=42),
        )
        plt.show()
