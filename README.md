Wandern is a small database migration tool for python.

# Database support

Wandern, for now, only supports PostgreSQL. Support for the following dialects
will be available soon.

-   MySQL
-   Sqlite
-   MSSQL


# Available Commands

- wandern init - Initialize wandern for your project
- wandern generate - Generate a new migration file
- wandern upgrade - Apply migrations (coming soon)
- wandern downgrade - Rollback migrations (coming soon)
- wandern reset - Reset all migrations
- wandern deinit - Remove wandern configuration
- wandern graph - Display migration dependency graph


## MVP

This is the document outlining the MVP (MInimum Viable Product) for Wandern.
For the first initial release, it should be able to do the following:

1. Ability to generate skeleton migration scripts with UP and DOWN revisions.
2. The migration scripts will be either SQL or Python.
3. Ability to keep track of the migration graph. And resolve conflicts if there are diverging branches.
4. Ability to migrate up and down a specific number of steps.
5. Ability to reset all migrations.

## Migration Graph Visualization

The `wandern graph` command provides a visual representation of your migration dependencies:

```bash
# Display the migration dependency tree
wandern graph

# Show only summary statistics
wandern graph --summary

# Override migration directory
wandern graph --directory path/to/migrations
```

This command helps you:
- Understand migration execution order
- Detect circular dependencies
- Identify isolated migrations
- Visualize the migration tree structure


For Future releases:
1. Ability to detect dialect-specific SQL code and suggest changes


## How to generate migration files

1. run `wandern generate` to create an empty migration script with default file name.
2. can be configured via wandern settings.
3. can set custom file names in settings. For example, {version}_{description}_{timestamp}.sql


### Fields that can be set
1. `version` - version number for each migration, can be integer
2.
