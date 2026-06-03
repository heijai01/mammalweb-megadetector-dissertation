"""Database connection helpers."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

from .config import DatabaseSettings, load_settings


def create_db_engine(settings: DatabaseSettings | None = None) -> Engine:
    """Create a SQLAlchemy engine for the remote MammalWeb database."""

    settings = settings or load_settings()
    connect_args = {}
    if settings.sslmode:
        connect_args["sslmode"] = settings.sslmode

    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True,
    )


def test_connection(engine: Engine) -> bool:
    """Return True when the database accepts a simple read-only query."""

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one() == 1
