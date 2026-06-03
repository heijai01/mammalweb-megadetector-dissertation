"""Input/output helpers for phpMyAdmin CSV exports."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def list_raw_csvs(data_dir: str | Path = RAW_DATA_DIR) -> list[Path]:
    """Return CSV files available in the raw export folder."""

    data_path = Path(data_dir)
    if not data_path.exists():
        return []
    return sorted(path for path in data_path.glob("*.csv") if path.is_file())


def load_raw_csv(
    filename: str | Path,
    data_dir: str | Path = RAW_DATA_DIR,
    required_columns: Iterable[str] | None = None,
    **read_csv_kwargs,
) -> pd.DataFrame:
    """Load a CSV exported from phpMyAdmin and stored in data/raw."""

    path = Path(filename)
    if not path.is_absolute():
        path = Path(data_dir) / path
    return load_csv_export(path, required_columns=required_columns, **read_csv_kwargs)


def load_csv_export(
    path: str | Path,
    required_columns: Iterable[str] | None = None,
    **read_csv_kwargs,
) -> pd.DataFrame:
    """Load one exported CSV file and optionally validate expected columns."""

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV export not found: {csv_path}")

    data = pd.read_csv(csv_path, **read_csv_kwargs)
    if required_columns is not None:
        missing = sorted(set(required_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Missing required columns in {csv_path.name}: {missing}")
    return data


def save_processed_csv(
    data: pd.DataFrame,
    filename: str | Path,
    data_dir: str | Path = PROCESSED_DATA_DIR,
    index: bool = False,
) -> Path:
    """Save a cleaned or derived CSV to data/processed."""

    output_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(filename)
    if not output_path.is_absolute():
        output_path = output_dir / output_path
    data.to_csv(output_path, index=index)
    return output_path
