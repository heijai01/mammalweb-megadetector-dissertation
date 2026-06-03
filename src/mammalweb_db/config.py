"""Environment variable handling for remote MammalWeb database access."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class DatabaseSettings:
    """Connection and query settings loaded from environment variables."""

    database_url: str
    schema: str | None = None
    query_limit: int = 1000
    images_table: str | None = None
    detections_table: str | None = None
    labels_table: str | None = None


def load_settings(env_file: str | Path = ".env") -> DatabaseSettings:
    """Load settings from a local .env file and the process environment."""

    load_dotenv(env_file)

    database_url = os.getenv("MAMMALWEB_DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "MAMMALWEB_DATABASE_URL is not set. Copy .env.example to .env and add the MySQL database URL."
        )

    return DatabaseSettings(
        database_url=database_url,
        schema=_blank_to_none(os.getenv("MAMMALWEB_DB_SCHEMA")),
        query_limit=int(os.getenv("MAMMALWEB_QUERY_LIMIT", "1000")),
        images_table=_blank_to_none(os.getenv("MAMMALWEB_IMAGES_TABLE")),
        detections_table=_blank_to_none(os.getenv("MAMMALWEB_DETECTIONS_TABLE")),
        labels_table=_blank_to_none(os.getenv("MAMMALWEB_LABELS_TABLE")),
    )


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
