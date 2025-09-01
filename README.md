# Wandern
<div align="center">
    <p>
      <a href="https://codecov.io/gh/s-bose/wandern" >
         <img src="https://codecov.io/gh/s-bose/wandern/branch/master/graph/badge.svg?token=X1ZE17QCFJ"/></a>
      <a href="https://github.com/s-bose/wandern/actions/workflows/tests.yml">
         <img src="https://github.com/s-bose/wandern/actions/workflows/tests.yml/badge.svg"></a>
      <a href="https://www.codefactor.io/repository/github/s-bose/wandern">
         <img src="https://www.codefactor.io/repository/github/s-bose/wandern/badge" alt="CodeFactor">
      </a>
    </p>
</div>

Wandern is a database migration tool written in Python.


## Supported Databases

- PostgreSQL
- SQLite
- MySQL (coming soon)
- MSSQL (coming soon)

## Commands

### `wandern init [directory]`
Initialize wandern for a new project.

**Options:**
- `--interactive`, `-i` - Run initialization in interactive mode
- `directory` - Path to the directory to contain migration scripts (optional)

### `wandern generate`
Generate a new migration file.

**Options:**
- `--message`, `-m` - Brief description of the migration
- `--author`, `-a` - Author of the migration (defaults to system user)
- `--tags`, `-t` - Comma-separated list of tags
- `--prompt`, `-p` - Autogenerate migration using natural language prompt

### `wandern up`
Apply pending migrations to the database.

**Options:**
- `--steps` - Number of migration steps to apply
- `--tags`, `-t` - Apply only migrations with specified tags
- `--author`, `-a` - Apply only migrations by specified author

### `wandern down`
Roll back applied migrations.

**Options:**
- `--steps` - Number of migration steps to roll back (default: all)

### `wandern reset`
Reset all migrations by rolling back all applied migrations.

### `wandern browse`
Browse database migrations interactively with filtering options.

**Options:**
- `--all`, `-A` - Include all migrations (both local and database)

## Installation

```bash
pip install wandern
```

## Quick Start

1. Initialize wandern in your project:
   ```bash
   wandern init
   ```

2. Generate your first migration:
   ```bash
   wandern generate --message "create users table"
   ```

3. Apply migrations:
   ```bash
   wandern up
   ```
