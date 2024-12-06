import pytest
import networkx as nx
from wandern.graph_builder import DAGBuilder
from wandern.exceptions import DivergentbranchError


def test_divergent_branch():
    builder = DAGBuilder(migration_dir="abc")

    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")
    dg.add_edge("c", "e")

    builder.graph = dg
    with pytest.raises(DivergentbranchError):
        builder.is_graph_diverging()


def test_loops_in_branch():
    builder = DAGBuilder(migration_dir="abc")

    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")
    dg.add_edge("d", "a")

    builder.graph = dg

    assert builder.get_cycles()


def test_no_loops():
    builder = DAGBuilder(migration_dir="abc")

    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")

    builder.graph = dg

    assert not builder.get_cycles()
    assert not builder.is_graph_diverging()
