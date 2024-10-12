Wandern is a small database migration tool for python.

# Database support

Wandern, for now, only supports PostgreSQL. Support for the following dialects
will be available soon.

-   MySQL
-   Sqlite
-   MSSQL


# Available Commands

- wandern migrate up -N num
- wandern migrate down -N num
- wandern migrate status
- wandern migrate up <version>
- wandern reset
- wandern generate
- wandern version
- wandern help


## MVP

This is the document outlining the MVP (MInimum Viable Product) for Wandern.
For the first initial release, it should be able to do the following:

1. Ability to generate skeleton migration scripts with UP and DOWN revisions.
2. The migration scripts will be either SQL or Python.
3. Ability to keep track of the migration graph. And resolve conflicts if there are diverging branches.
4. Ability to migrate up and down a specific number of steps.
5. Ability to reset all migrations.


For Future releases:
1. Ability to detect dialect-specific SQL code and suggest changes
