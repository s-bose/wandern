import pytest
import networkx as nx
from wandern.graph import MigrationGraph
from wandern.exceptions import DivergentbranchError, CycleDetected
from wandern.models import Revision


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

    with pytest.raises(CycleDetected):
        MigrationGraph.check_cycles(dg)


def test_no_loops():
    dg = nx.DiGraph()

    dg.add_edge("a", "b")
    dg.add_edge("b", "c")
    dg.add_edge("c", "d")

    assert not MigrationGraph.check_cycles(dg)


def test_migration_files():
    migration_dir = "tests/migrations"
    graph = MigrationGraph.build(migration_dir)
    assert graph
    last_migration = graph.get_last_migration()
    assert last_migration

    assert last_migration.revision_id == "0005"


def test_iter():
    migration_dir = "tests/migrations"
    graph = MigrationGraph.build(migration_dir)
    assert graph

    revisions = list(graph.iter())
    assert len(revisions) > 0
    assert all(isinstance(rev, Revision) for rev in revisions)

    # Check that the revisions are in the expected order
    expected_ids = {"0001", "0002", "0003", "0004", "0005"}
    assert {rev.revision_id for rev in revisions} == expected_ids

    rev_iterator = graph.iter()

    first = next(rev_iterator)
    assert first.revision_id == "0001"
    assert first.down_revision_id is None

    second = next(rev_iterator)
    assert second.revision_id == "0002"
    assert second.down_revision_id == "0001"

    third = next(rev_iterator)
    assert third.revision_id == "0003"
    assert third.down_revision_id == "0002"

    fourth = next(rev_iterator)
    assert fourth.revision_id == "0004"
    assert fourth.down_revision_id == "0003"

    fifth = next(rev_iterator)
    assert fifth.revision_id == "0005"
    assert fifth.down_revision_id == "0004"

    with pytest.raises(StopIteration):
        next(rev_iterator)


def test_iter_from():
    migration_dir = "tests/migrations"
    graph = MigrationGraph.build(migration_dir)
    assert graph

    revisions = list(graph.iter_from("0003"))
    assert len(revisions) > 0
    assert all(isinstance(rev, Revision) for rev in revisions)

    # Check that the revisions are in the expected order
    expected_ids = {"0004", "0005"}
    assert {rev.revision_id for rev in revisions} == expected_ids
