init_migration_table: str = """
CREATE TABLE IF NOT EXISTS wandern_migration (
    id varchar PRIMARY KEY NOT NULL,
    down_revision varchar NULL,
)
"""
