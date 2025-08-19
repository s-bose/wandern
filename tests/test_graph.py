import pytest
import networkx as nx
from wandern.graph import MigrationGraph
from wandern.exceptions import DivergentbranchError


def test_divergent_branch():
    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")
    dg.add_edge("c", "e")

    migration_graph = MigrationGraph(dg)
    with pytest.raises(DivergentbranchError):
        migration_graph.get_last_migration()


def test_loops_in_branch():
    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")
    dg.add_edge("d", "b")

    graph = MigrationGraph(dg)

    cycle = graph.get_cycles()
    assert cycle
    assert cycle == [
        ("b", "c", "forward"),
        ("c", "d", "forward"),
        ("d", "b", "forward"),
    ]


def test_no_loops():
    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")

    graph = MigrationGraph(dg)

    assert not graph.get_cycles()


def test_migration_files():
    migration_dir = "tests/migrations"
    graph = MigrationGraph.build(migration_dir)
    assert graph
    last_migration = graph.get_last_migration()
    assert last_migration

    assert last_migration == "0005"
