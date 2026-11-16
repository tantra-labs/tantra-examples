"""Canonical data-root layout for the provisioning service (plan 0004).

The service provisions a *data root* (the ``$VYAAPAAR_DATA_DIR`` layout). Every
consumer in the workspace resolves this same root:

* ``tantra.store.find_data_root`` / ``$VYAAPAAR_DATA_DIR`` (wheel, sim, analyser,
  UI ``data_dir``, testing adapter);
* ``tantra_examples.screening.paths`` (screeners: ``find_catalog_path`` /
  ``find_duckdb_path`` / ``find_mutual_funds_db_path``).

This module is the single source of truth for the layout the provisioner writes.
"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

DATA_DIR_ENV = "VYAAPAAR_DATA_DIR"
"""Environment variable naming the data root (beats cwd discovery, matches
``tantra.store`` and ``tantra_examples.screening.paths``)."""


class Dataset(StrEnum):
    """The three datasets the provisioning service can provision."""

    NSE_1D_CATALOG = "nse_1d_catalog"
    FUNDAMENTALS = "fundamentals"
    MUTUAL_FUNDS = "mutual_funds"


class Mode(StrEnum):
    """The three provisioning modes (plan 0004)."""

    DOWNLOAD = "download"
    DUMMY = "dummy"
    MONTE_CARLO = "monte-carlo"


def resolve_data_root(explicit: str | Path | None = None) -> Path:
    """Resolve the data root without creating it (pure).

    Priority: ``explicit`` argument > ``$VYAAPAAR_DATA_DIR`` > wheel
    :func:`tantra.store.find_data_root` (cwd/project discovery).
    """
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get(DATA_DIR_ENV, "").strip()
    if env:
        return Path(env).expanduser().resolve()
    try:
        from tantra.store import find_data_root

        return find_data_root()
    except ImportError:
        return Path.cwd() / "data"


def catalog_dir(root: str | Path) -> Path:
    """``<root>/catalog/1D/NSE`` — the 1D NSE price catalog directory."""
    return Path(root) / "catalog" / "1D" / "NSE"


def fundamentals_db(root: str | Path) -> Path:
    """``<root>/fundamentals.duckdb`` — the fundamentals DuckDB file."""
    return Path(root) / "fundamentals.duckdb"


def mutual_funds_db(root: str | Path) -> Path:
    """``<root>/mutual_funds.duckdb`` — the mutual-funds DuckDB file."""
    return Path(root) / "mutual_funds.duckdb"


def symbol_year_path(root: str | Path, symbol: str, year: int) -> Path:
    """``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet`` for one symbol-year."""
    return catalog_dir(root) / symbol.upper() / f"{year}.parquet"


__all__ = [
    "DATA_DIR_ENV",
    "Dataset",
    "Mode",
    "catalog_dir",
    "fundamentals_db",
    "mutual_funds_db",
    "resolve_data_root",
    "symbol_year_path",
]
