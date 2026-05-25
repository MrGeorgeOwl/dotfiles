---
name: dashboards-api-migrations
description: Use when creating or changing Alembic migrations in the SplitMetrics dashboards-api repository.
---

# Dashboards API Migrations

## Overview

Use this skill for dashboards-api Alembic migrations. The repo stores analytical/reference data in StarRocks, so migrations should follow local StarRocks DDL style and the existing Alembic revision chain.

## Workflow

1. Start from an updated base branch when creating a new branch. Check `git status --short --branch` first and do not disturb unrelated user files.
2. Inspect nearby migrations before editing:
   - `poetry run alembic -c alembic.ini history`
   - `ls -1 alembic/versions`
   - `rg -n "CREATE TABLE|ORDER BY|PRIMARY KEY|DISTRIBUTED BY|<table-or-column>" alembic/versions src tests`
3. Name new migration files as `<revision>_<order>_<slug>.py`, where `<order>` comes from the actual `alembic history` chain, not just the largest filename number.
4. For a new table migration, set `down_revision` to the current Alembic head and choose the schema from the surrounding migrations or the requested target table.
5. Verify with at least:
   - `poetry run ruff check <migration-files>`
   - `poetry run python -m py_compile <migration-files>`
   - `poetry run alembic -c alembic.ini heads`
   - `poetry run alembic -c alembic.ini history`

Always pass `-c alembic.ini` when manipulating migrations so Alembic uses the repository configuration intentionally.

## StarRocks DDL

- Use uppercase SQL type names in new DDL: `INT(11)`, `BIGINT(20)`, `VARCHAR`, `DATETIME`, `BOOLEAN`, `JSON`.
- For Kafka-replicated reference tables, make every column nullable except the primary key column unless the user or an existing source DDL requires otherwise.
- Keep table DDL close to existing StarRocks patterns, including bitmap indexes for common relationship/filter columns when surrounding migrations use them.
- Make migrations idempotent where possible: create objects only if they do not exist, drop objects only if they exist, and add/drop/modify columns defensively with the repo's helper functions or equivalent guards.
- Drop dependent objects in reverse dependency order during downgrade.
- Mirror source PostgreSQL/Django types logically:
  - PostgreSQL `int4` / Django `AutoField` -> StarRocks `INT(11)`
  - PostgreSQL `int8` / Django `BigAutoField` -> StarRocks `BIGINT(20)`
  - PostgreSQL `timestamp` -> StarRocks `DATETIME`
  - PostgreSQL `numeric(p, s)` -> StarRocks `DECIMAL(p, s)` unless existing migrations intentionally differ
- Use generated columns for JSON-derived access only when the surrounding query code or existing table pattern needs them. Ask the user how they expect new generated columns to be defined/created before adding them.
- In StarRocks `CREATE TABLE`, define all ordinary columns before generated columns; place generated columns after ordinary columns and before indexes/keys.

## ORDER BY / Sort Key

StarRocks `ORDER BY` defines the sort key and prefix index. Choose it from expected query filters, not automatically from the primary key.

- Prefer columns frequently used in filter conditions.
- Order sort-key columns by descending filter frequency.
- Keep the key short; about three columns is a good target and more than four is usually not worth the load/sort cost.
- If filter frequency is similar, consider cardinality: higher cardinality can prune more data, while lower cardinality can compress better.
- Put at most one `CHAR`/`VARCHAR`/`STRING` field in the prefix-relevant part, and put it at the end.
- If no good non-primary access pattern exists, omit `ORDER BY` or use the local table pattern already established for similar tables.

For soft-removable reference tables, `date_removed` is commonly first when active-row filtering is a major access path. For child lookup tables, parent IDs usually belong before locale/status strings.

## Common Pitfalls

- Do not infer the migration order from filenames alone; use `poetry run alembic -c alembic.ini history`.
- Do not make non-ID columns `NOT NULL` for Kafka-replicated reference tables without a source DDL reason.
- Do not place a string column first in `ORDER BY` unless it is truly the dominant filter.
- Do not use lowercase type names in new DDL.
- Do not interleave generated columns with ordinary columns; StarRocks rejects tables unless all generated columns are defined after ordinary columns.
- Do not rely on `ORDER BY(id)` for Primary Key tables when business filters are known; StarRocks allows a separate sort key because primary keys usually do not accelerate scans by themselves.
