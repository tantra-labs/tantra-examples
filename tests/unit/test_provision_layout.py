"""Unit: canonical provision layout constants and data-root resolution (plan 0004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tantra_examples.provision.layout import (
    DATA_DIR_ENV,
    Dataset,
    Mode,
    catalog_dir,
    fundamentals_db,
    mutual_funds_db,
    resolve_data_root,
    symbol_year_path,
)


def test_dataset_enum_values() -> None:
    assert Dataset.NSE_1D_CATALOG == "nse_1d_catalog"
    assert Dataset.FUNDAMENTALS == "fundamentals"
    assert Dataset.MUTUAL_FUNDS == "mutual_funds"


def test_mode_enum_values() -> None:
    assert Mode.DOWNLOAD == "download"
    assert Mode.DUMMY == "dummy"
    assert Mode.MONTE_CARLO == "monte-carlo"


def test_canonical_layout_paths(tmp_path: Path) -> None:
    root = tmp_path / "root"
    assert catalog_dir(root) == root / "catalog" / "1D" / "NSE"
    assert fundamentals_db(root) == root / "fundamentals.duckdb"
    assert mutual_funds_db(root) == root / "mutual_funds.duckdb"
    year_path = root / "catalog" / "1D" / "NSE" / "RELIANCE" / "2024.parquet"
    assert symbol_year_path(root, "reliance", 2024) == year_path


def test_resolve_data_root_env_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    assert resolve_data_root() == tmp_path.resolve()


def test_resolve_data_root_explicit_beats_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    explicit = tmp_path / "other"
    assert resolve_data_root(explicit) == explicit.resolve()


def test_resolve_data_root_ignores_blank_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, "   ")
    root = resolve_data_root()
    assert isinstance(root, Path)
    assert root.is_absolute()


def test_resolve_data_root_no_env_uses_wheel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    from tantra.store import find_data_root

    assert resolve_data_root() == find_data_root().resolve()
