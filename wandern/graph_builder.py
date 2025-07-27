import os
from pathlib import Path
import networkx as nx
from wandern.exceptions import DivergentbranchError, InvalidMigrationFile, CycleDetected

from wandern.constants import REGEX_REVISION_ID


class MigrationGraph:
    def __init__(self, graph: nx.DiGraph):
        self._graph = graph

    @classmethod
    def build(cls, migration_dir: str):
        graph = nx.DiGraph()

        revision_id, down_revision_id = None, None
        for index, file in enumerate(
            sorted(Path(migration_dir).iterdir(), key=os.path.getmtime)
        ):

            if not os.path.isfile(file) or file.suffix != ".sql":
                raise InvalidMigrationFile("Migration file must be a sql file")

            with open(file, "r") as f:
                content = f.read()

                match = REGEX_REVISION_ID.search(content)
                if not match:
                    raise InvalidMigrationFile("Missing revision id")

                revision_id = match.group("revision_id")
                down_revision_id = match.group("down_revision_id")

                graph.add_edge(down_revision_id, revision_id, index=index)

        return cls(graph=graph)

    def get_last_migration(self):
        if cycle := self.get_cycles():
            raise CycleDetected(cycle)

        for u, v in self._graph.edges():

            out_edges = self._graph.out_edges(v)
            print(f"{u=} {v=} {out_edges=}")

            if len(out_edges) > 1:
                raise DivergentbranchError(from_=v, to_=[node[1] for node in out_edges])

            if len(out_edges) == 0:
                return u, v

        return None

    def get_cycles(self):
        try:
            cycle = nx.find_cycle(self._graph, orientation="original")
            print(f"{cycle=}")
            return cycle
        except nx.NetworkXNoCycle:
            return None

    # def show_ascii_graph(self):
    #     """Display the migration graph as ASCII art in the terminal."""
    #     if not self.graph.nodes:
    #         print("No migrations found in the graph.")
    #         return

    #     # Find the root node (node with no incoming edges)
    #     root_nodes = [
    #         node for node in self.graph.nodes if self.graph.in_degree(node) == 0
    #     ]

    #     if not root_nodes:
    #         print("Warning: No root migration found (circular dependency detected)")
    #         root_nodes = list(self.graph.nodes)[:1]

    #     print("\nMigration Graph (ASCII):")
    #     print("=" * 50)

    #     # Track visited nodes to avoid infinite loops
    #     visited = set()

    #     def print_tree(node, prefix="", is_last=True, level=0):
    #         if node in visited:
    #             return
    #         visited.add(node)

    #         # Create the tree structure
    #         connector = "└── " if is_last else "├── "
    #         print(f"{prefix}{connector}{node}")

    #         # Get children (nodes this migration leads to)
    #         children = list(self.graph.successors(node))

    #         if children:
    #             # Sort children for consistent display
    #             children.sort()

    #             for i, child in enumerate(children):
    #                 is_child_last = i == len(children) - 1
    #                 extension = "    " if is_last else "│   "
    #                 print_tree(child, prefix + extension, is_child_last, level + 1)

    #     # Handle multiple root nodes
    #     for i, root in enumerate(sorted(root_nodes)):
    #         if i > 0:
    #             print()  # Add spacing between multiple trees
    #         print_tree(root, "", True)

    #     # Show additional graph statistics
    #     print("\nGraph Statistics:")
    #     print(f"Total migrations: {len(self.graph.nodes)}")
    #     print(f"Migration connections: {len(self.graph.edges)}")

    #     # Check for cycles
    #     cycles = self.get_cycles()
    #     if cycles:
    #         print(f"⚠️  Cycles detected: {cycles}")
    #     else:
    #         print("✅ No cycles detected")

    #     # Show isolated nodes (if any)
    #     isolated = list(nx.isolates(self.graph))
    #     if isolated:
    #         print(f"⚠️  Isolated migrations: {isolated}")
