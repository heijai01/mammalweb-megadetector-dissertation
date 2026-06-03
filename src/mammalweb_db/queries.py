"""Read-only query utilities for MammalWeb exploratory analysis."""

from __future__ import annotations

import re
from typing import Any, Mapping

import pandas as pd
from sqlalchemy import Engine, text

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def list_schemas(engine: Engine) -> pd.DataFrame:
    """Return non-system MySQL/MariaDB databases visible to the current user."""

    sql = """
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
    ORDER BY schema_name
    """
    return read_sql(engine, sql)


def list_tables(engine: Engine, schema: str | None = None) -> pd.DataFrame:
    """Return base tables visible to the current database user."""

    sql = """
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE'
      AND (:schema IS NULL OR table_schema = :schema)
    ORDER BY table_schema, table_name
    """
    return read_sql(engine, sql, {"schema": schema})


def describe_table(engine: Engine, table_name: str, schema: str | None = None) -> pd.DataFrame:
    """Return column names and types for one table."""

    sql = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = :table_name
      AND (:schema IS NULL OR table_schema = :schema)
    ORDER BY ordinal_position
    """
    return read_sql(engine, sql, {"table_name": table_name, "schema": schema})


def sample_table(
    engine: Engine,
    table_name: str,
    schema: str | None = None,
    limit: int = 20,
) -> pd.DataFrame:
    """Return a small sample from a table after validating identifiers."""

    table_ref = qualified_name(table_name, schema)
    sql = f"SELECT * FROM {table_ref} LIMIT :limit"
    return read_sql(engine, sql, {"limit": limit})


def read_sql(
    engine: Engine,
    sql: str,
    params: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Run a read-only SQL query and return a pandas DataFrame."""

    if not sql.lstrip().lower().startswith("select"):
        raise ValueError("Only SELECT queries should be run through this helper.")

    with engine.connect() as connection:
        return pd.read_sql_query(text(sql), connection, params=dict(params or {}))


def qualified_name(table_name: str, schema: str | None = None) -> str:
    """Build a safely quoted MySQL/MariaDB schema-qualified table name."""

    parts = [part for part in (schema, table_name) if part]
    for part in parts:
        if not _IDENTIFIER.fullmatch(part):
            raise ValueError(f"Unsafe SQL identifier: {part!r}")
    return ".".join(f"`{part}`" for part in parts)
