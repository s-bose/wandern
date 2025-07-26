from typing import Pattern
import os
import re
import networkx as nx

try:
    from matplotlib import pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from wandern.exceptions import DivergentbranchError


class DAGBuilder:
    def __init__(self, migration_dir: str):
        self.migration_dir = migration_dir

        self.regex_revision_ids: Pattern = re.compile(
            r"Revision ID: (?P<revision_id>\w+)\nRevises: (?P<down_revision_id>\w+)"
        )

        self.graph = nx.DiGraph()

    def iterate(self) -> tuple[str, str]:
        revision_id, down_revision_id = None, None
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

        return revision_id, down_revision_id

    def show_graph(self):
        if not HAS_MATPLOTLIB:
            print("Matplotlib not available. Use 'show_ascii_graph()' instead.")
            return

        try:
            from matplotlib import pyplot as plt
            nx.draw(
                self.graph,
                nodelist=list(self.graph.nodes),
                node_size=[len(node) * 500 for node in list(self.graph.nodes)],
                with_labels=True,
                pos=nx.spring_layout(self.graph, seed=42),
            )
            plt.show()
        except ImportError:
            print("Matplotlib not available. Use 'show_ascii_graph()' instead.")

    def get_cycles(self):
        try:
            cycle = nx.find_cycle(self.graph, orientation="original")
            return cycle
        except nx.NetworkXNoCycle:
            return None

    def show_ascii_graph(self):
        """Display the migration graph as ASCII art in the terminal."""
        if not self.graph.nodes:
            print("No migrations found in the graph.")
            return

        # Find the root node (node with no incoming edges)
        root_nodes = [node for node in self.graph.nodes if self.graph.in_degree(node) == 0]

        if not root_nodes:
            print("Warning: No root migration found (circular dependency detected)")
            root_nodes = list(self.graph.nodes)[:1]

        print("\nMigration Graph (ASCII):")
        print("=" * 50)

        # Track visited nodes to avoid infinite loops
        visited = set()

        def print_tree(node, prefix="", is_last=True, level=0):
            if node in visited:
                return
            visited.add(node)

            # Create the tree structure
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{node}")

            # Get children (nodes this migration leads to)
            children = list(self.graph.successors(node))

            if children:
                # Sort children for consistent display
                children.sort()

                for i, child in enumerate(children):
                    is_child_last = (i == len(children) - 1)
                    extension = "    " if is_last else "│   "
                    print_tree(child, prefix + extension, is_child_last, level + 1)

        # Handle multiple root nodes
        for i, root in enumerate(sorted(root_nodes)):
            if i > 0:
                print()  # Add spacing between multiple trees
            print_tree(root, "", True)

        # Show additional graph statistics
        print("\nGraph Statistics:")
        print(f"Total migrations: {len(self.graph.nodes)}")
        print(f"Migration connections: {len(self.graph.edges)}")

        # Check for cycles
        cycles = self.get_cycles()
        if cycles:
            print(f"⚠️  Cycles detected: {cycles}")
        else:
            print("✅ No cycles detected")

        # Show isolated nodes (if any)
        isolated = list(nx.isolates(self.graph))
        if isolated:
            print(f"⚠️  Isolated migrations: {isolated}")

    def is_graph_diverging(self):
        for node in self.graph.nodes:
            out_edges = self.graph.out_edges(node)

            out_nodes = ", ".join(node[1] for node in list(out_edges))

            if len(out_edges) > 1:
                raise DivergentbranchError(
                    f"Diverging migration found {node} -> {out_nodes}"
                )

        return False
