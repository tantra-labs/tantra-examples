"""Unit tests for the Monte-Carlo provisioning mode (plan 0004, T15.3)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from tantra_examples.provision.contracts import ProvisionRequest
from tantra_examples.provision.dummy import is_complete
from tantra_examples.provision.layout import Dataset, Mode, catalog_dir, fundamentals_db
from tantra_examples.provision.monte_carlo import provision_monte_carlo

RELIANCE = "RELIANCE"


@pytest.fixture()
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``$TANTRA_DATA_DIR`` at ``tmp_path`` and return it."""

    monkeypatch.setenv("TANTRA_DATA_DIR", str(tmp_path))
    return tmp_path


def _request(data_root: Path, *, seed: int | None, force: bool = False) -> ProvisionRequest:
    return ProvisionRequest(
        dataset=Dataset.NSE_1D_CATALOG,
        mode=Mode.MONTE_CARLO,
        seed=seed,
        data_root=data_root,
        force=force,
    )


def _rel_parquet(root: Path, year: int) -> Path:
    return catalog_dir(root) / RELIANCE / f"{year}.parquet"


def _first_close(parquet: Path) -> Decimal:
    with duckdb.connect() as conn:
        row = conn.execute(
            "SELECT close FROM read_parquet(?) ORDER BY ts LIMIT 1",
            [str(parquet)],
        ).fetchone()
    assert row is not None
    return row[0]


def _closes(conn: duckdb.DuckDBPyConnection, parquet: Path) -> list[Decimal]:
    return [
        row[0]
        for row in conn.execute(
            "SELECT close FROM read_parquet(?) ORDER BY ts LIMIT 20",
            [str(parquet)],
        ).fetchall()
    ]


def test_same_seed_is_reproducible(data_root: Path) -> None:
    """A fixed seed must produce byte-identical parquet across roots."""

    root_a = data_root / "a"
    root_b = data_root / "b"
    provision_monte_carlo(_request(root_a, seed=7))
    provision_monte_carlo(_request(root_b, seed=7))
    assert is_complete(root_a)
    assert is_complete(root_b)
    assert _rel_parquet(root_a, 2024).read_bytes() == _rel_parquet(root_b, 2024).read_bytes()


def test_different_seeds_differ(data_root: Path) -> None:
    """Different seeds must produce different close paths."""

    root_a = data_root / "a"
    root_b = data_root / "b"
    provision_monte_carlo(_request(root_a, seed=1))
    provision_monte_carlo(_request(root_b, seed=2))
    assert _first_close(_rel_parquet(root_a, 2020)) != _first_close(_rel_parquet(root_b, 2020))


def test_seed_none_is_truly_random(data_root: Path) -> None:
    """Two unseeded runs must produce different (random) close paths."""

    root_a = data_root / "a"
    root_b = data_root / "b"
    job_a = provision_monte_carlo(_request(root_a, seed=None))
    job_b = provision_monte_carlo(_request(root_b, seed=None))
    assert job_a.status == "done"
    assert job_b.status == "done"
    with duckdb.connect() as conn:
        closes_a = _closes(conn, _rel_parquet(root_a, 2020))
        closes_b = _closes(conn, _rel_parquet(root_b, 2020))
    assert closes_a != closes_b


def test_layout_and_decimal_schema(data_root: Path) -> None:
    """Layout, decimal schema, and fundamentals DB must match the dummy mode."""

    job = provision_monte_carlo(_request(data_root, seed=3))
    assert job.status == "done"
    for year in range(2020, 2026):
        assert _rel_parquet(data_root, year).is_file()
    with duckdb.connect() as conn:
        columns = conn.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(_rel_parquet(data_root, 2024))],
        ).fetchall()
    column_types = {column[0]: column[1] for column in columns}
    assert column_types["ts"] == "BIGINT"
    for name in ("open", "close", "volume"):
        assert column_types[name].startswith("DECIMAL")
    assert fundamentals_db(data_root).is_file()


def test_skips_when_complete(data_root: Path) -> None:
    """A complete root must be skipped unless ``force=True``."""

    first = provision_monte_carlo(_request(data_root, seed=5))
    assert first.status == "done"
    second = provision_monte_carlo(_request(data_root, seed=5))
    assert second.status == "skipped"
    forced = provision_monte_carlo(_request(data_root, seed=5, force=True))
    assert forced.status == "done"


def test_unsupported_dataset_raises(data_root: Path) -> None:
    """Unsupported datasets must raise NotImplementedError."""

    request = ProvisionRequest(
        dataset=Dataset.FUNDAMENTALS,
        mode=Mode.MONTE_CARLO,
        seed=1,
        data_root=data_root,
    )
    with pytest.raises(NotImplementedError, match="not wired yet"):
        provision_monte_carlo(request)
