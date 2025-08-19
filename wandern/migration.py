from wandern.config import Config
from wandern.databases.provider import get_database_impl
from wandern.graph import MigrationGraph
from wandern.types import Revision


def migrate_up(config: Config, steps: int | None = None):
    database_helper = get_database_impl(config.dialect, config=config)

    mg = MigrationGraph.build(config.migration_dir)

    # Apply create table migrations first
    database_helper.create_table_migration()

    head_revision = database_helper.get_head_revision()
    if not head_revision:
        # first migration
        start_nodes = [
            node for node, in_degree in mg._graph.in_degree() if in_degree == 0
        ]

        if len(start_nodes) > 1:
            raise ValueError("Multiple first revisions found")

        start_node = start_nodes[0]

    else:
        head_rev_id = head_revision.get("id")
        if not mg._graph:  # TODO
            raise ValueError()

        head_rev_node = mg._graph.nodes.get(head_rev_id)
        if not head_rev_node:  # TODO
            raise ValueError()

        start_node = next(mg._graph.successors(head_rev_id))

    if not steps:
        # until the end of files
        while mg._graph.out_degree(start_node) != 0:
            revision = Revision(**mg._graph.nodes[start_node])
            database_helper.migrate_up(revision)
            start_node = next(mg._graph.successors(start_node))

    else:
        for i in range(steps):
            revision = Revision(**mg._graph.nodes[start_node])
            database_helper.migrate_up(revision)
            start_node = next(mg._graph.successors(start_node))


def migrate_down(config: Config, steps: int | None = None):
    database_helper = get_database_impl(config.dialect, config=config)

    mg = MigrationGraph.build(config.migration_dir)

    # Apply create table migrations first
    database_helper.create_table_migration()

    head_revision = database_helper.get_head_revision()

    if not head_revision:
        return  # Nothing to down revise from
