import networkx as nx
import pytest

from wandern.exceptions import CycleDetected, DivergentbranchError, InvalidMigrationFile
from wandern.graph import MigrationGraph
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
    migration_dir = "tests/fixtures/migrations"
    graph = MigrationGraph.build(migration_dir)
    assert graph
    last_migration = graph.get_last_migration()
    assert last_migration

    assert last_migration.revision_id == "0005"


def test_iter():
    migration_dir = "tests/fixtures/migrations"
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
    migration_dir = "tests/fixtures/migrations"
    graph = MigrationGraph.build(migration_dir)
    assert graph

    revisions = list(graph.iter_from("0003"))
    assert len(revisions) > 0
    assert all(isinstance(rev, Revision) for rev in revisions)

    # Check that the revisions are in the expected order
    expected_ids = {"0004", "0005"}
    assert {rev.revision_id for rev in revisions} == expected_ids


def test_iter_from_invalid_revision():
    """Test iter_from with non-existent revision ID."""
    migration_dir = "tests/fixtures/migrations"
    graph = MigrationGraph.build(migration_dir)

    with pytest.raises(
        ValueError, match="Revision: nonexistent does not exist in the graph"
    ):
        list(graph.iter_from("nonexistent"))


def test_get_node():
    """Test getting a specific node from the graph."""
    migration_dir = "tests/fixtures/migrations"
    graph = MigrationGraph.build(migration_dir)

    # Test existing node
    revision = graph.get_node("0003")
    assert revision is not None
    assert revision.revision_id == "0003"
    assert isinstance(revision, Revision)

    # Test non-existent node
    revision = graph.get_node("nonexistent")
    assert revision is None


def test_first_property():
    """Test the first property returns the root node."""
    migration_dir = "tests/fixtures/migrations"
    graph = MigrationGraph.build(migration_dir)

    first_id = graph.first
    assert first_id == "0001"


def test_first_property_empty_graph():
    """Test first property with empty graph."""
    empty_graph = nx.DiGraph()
    migration_graph = MigrationGraph(empty_graph)

    assert migration_graph.first is None


def test_get_last_migration_single_node():
    """Test get_last_migration with a single node graph."""
    dg = nx.DiGraph()
    dg.add_node("single", revision_id="single", down_revision_id=None, message="test")

    migration_graph = MigrationGraph(dg)
    last = migration_graph.get_last_migration()

    assert last is not None
    assert last.revision_id == "single"


def test_get_last_migration_empty_graph():
    """Test get_last_migration with empty graph."""
    empty_graph = nx.DiGraph()
    migration_graph = MigrationGraph(empty_graph)

    last = migration_graph.get_last_migration()
    assert last is None


def test_iter_empty_graph():
    """Test iter with empty graph."""
    empty_graph = nx.DiGraph()
    migration_graph = MigrationGraph(empty_graph)

    revisions = list(migration_graph.iter())
    assert revisions == []


def test_iter_single_node():
    """Test iter with single node graph."""
    dg = nx.DiGraph()
    dg.add_node(
        "single",
        revision_id="single",
        down_revision_id=None,
        message="test",
        author=None,
        tags=None,
        up_sql="",
        down_sql="",
        created_at="2024-01-01T00:00:00",
    )

    migration_graph = MigrationGraph(dg)
    revisions = list(migration_graph.iter())

    assert len(revisions) == 1
    assert revisions[0].revision_id == "single"


def test_check_divergence_no_divergence():
    """Test check_divergence with valid linear graph."""
    dg = nx.DiGraph()
    dg.add_edge("a", "b")
    dg.add_edge("b", "c")

    # Should not raise any exception
    MigrationGraph.check_divergence(dg)


def test_check_cycles_no_cycles():
    """Test check_cycles returns None when no cycles exist."""
    dg = nx.DiGraph()
    dg.add_edge("a", "b")
    dg.add_edge("b", "c")

    result = MigrationGraph.check_cycles(dg)
    assert result is None


def test_build_with_non_sql_file(tmp_path):
    """Test MigrationGraph.build raises InvalidMigrationFile for non-SQL files."""
    # Create a temporary directory with a non-SQL file
    test_dir = tmp_path / "migrations"
    test_dir.mkdir()

    # Create a non-SQL file
    non_sql_file = test_dir / "test.txt"
    non_sql_file.write_text("This is not a SQL file")

    with pytest.raises(InvalidMigrationFile, match="Migration file must be a sql file"):
        MigrationGraph.build(str(test_dir))


def test_build_with_directory_in_migration_dir(tmp_path):
    """Test MigrationGraph.build raises InvalidMigrationFile for directories."""
    # Create a temporary directory with a subdirectory
    test_dir = tmp_path / "migrations"
    test_dir.mkdir()

    # Create a subdirectory instead of a file
    subdir = test_dir / "subdir"
    subdir.mkdir()

    with pytest.raises(InvalidMigrationFile, match="Migration file must be a sql file"):
        MigrationGraph.build(str(test_dir))


def test_build_with_invalid_sql_content(tmp_path):
    """Test MigrationGraph.build raises InvalidMigrationFile for unparseable SQL files."""
    from unittest.mock import patch

    # Create a temporary directory with an invalid SQL file
    test_dir = tmp_path / "migrations"
    test_dir.mkdir()

    # Create an SQL file that will cause parse_sql_file_content to raise ValueError
    invalid_sql_file = test_dir / "invalid.sql"
    invalid_sql_file.write_text("/*Invalid SQL content*/")

    # Mock parse_sql_file_content to raise ValueError
    with patch(
        "wandern.graph.parse_sql_file_content", side_effect=ValueError("Parse error")
    ):
        with pytest.raises(
            InvalidMigrationFile, match="Error parsing migration file: invalid.sql"
        ):
            MigrationGraph.build(str(test_dir))
