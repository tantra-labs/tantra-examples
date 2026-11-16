"""Unit: canonical dummy lakehouse generator (plan 0004 dummy mode)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from tantra_examples.provision import provision
from tantra_examples.provision.contracts import ProvisionJob, ProvisionRequest
from tantra_examples.provision.dummy import (
    COMPANY_NAMES,
    SESSION_END,
    SESSION_START,
    build_lakehouse,
    is_complete,
    sessions,
)
from tantra_examples.provision.layout import Dataset, Mode, catalog_dir, fundamentals_db


def test_sessions_are_weekdays_in_window() -> None:
    days = sessions()
    assert days[0] == SESSION_START
    assert days[-1] == SESSION_END
    assert all(d.weekday() < 5 for d in days)
    assert len(days) == len({d for d in days})  # no duplicates


def test_build_lakehouse_writes_canonical_layout(tmp_path: Path) -> None:
    root = tmp_path / "root"
    build_lakehouse(root)
    assert catalog_dir(root).is_dir()
    assert fundamentals_db(root).is_file()
    for symbol in COMPANY_NAMES:
        sym_dir = catalog_dir(root) / symbol
        parquets = sorted(sym_dir.glob("*.parquet"))
        assert parquets, symbol
        years = {p.stem for p in parquets}
        assert years == {str(y) for y in range(2020, 2026)}


def test_build_lakehouse_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "root"
    build_lakehouse(root)
    parquet_before = sorted(p for p in catalog_dir(root).rglob("*.parquet"))
    build_lakehouse(root)  # second call must not duplicate or fail
    parquet_after = sorted(p for p in catalog_dir(root).rglob("*.parquet"))
    assert parquet_before == parquet_after


def test_is_complete_flags_layout(tmp_path: Path) -> None:
    root = tmp_path / "root"
    assert is_complete(root) is False
    build_lakehouse(root)
    assert is_complete(root) is True


def test_dummy_catalog_is_decimal_canonical(tmp_path: Path) -> None:
    """Parquet OHLCV/volume columns are decimal128(38, 10) — the wheel BAR_SCHEMA."""
    root = tmp_path / "root"
    build_lakehouse(root)
    parquet = next((catalog_dir(root) / "RELIANCE").glob("*.parquet"))
    con = duckdb.connect()
    rows = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet}')").fetchall()
    con.close()
    types = {row[0]: row[1] for row in rows}
    assert types["open"].startswith("DECIMAL")
    assert types["close"].startswith("DECIMAL")
    assert types["volume"].startswith("DECIMAL")
    assert types["ts"] == "BIGINT"


def test_dummy_catalog_reads_exact_decimal(tmp_path: Path) -> None:
    root = tmp_path / "root"
    build_lakehouse(root)
    parquet = next((catalog_dir(root) / "RELIANCE").glob("*.parquet"))
    con = duckdb.connect()
    value = con.execute(
        f"SELECT close FROM read_parquet('{parquet}') ORDER BY ts LIMIT 1"
    ).fetchone()[0]
    con.close()
    assert isinstance(value, Decimal)


def test_dummy_fundamentals_decimal_schema(tmp_path: Path) -> None:
    root = tmp_path / "root"
    build_lakehouse(root)
    con = duckdb.connect(str(fundamentals_db(root)))
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    assert {"companies", "financial_ratios", "financial_statements"} <= tables
    cols = con.execute("DESCRIBE financial_ratios").fetchall()
    con.close()
    types = {row[0]: row[1] for row in cols}
    assert types["eps"].startswith("DECIMAL")
    assert types["roce_pct"].startswith("DECIMAL")


def test_provision_dummy_returns_done_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TANTRA_DATA_DIR", str(tmp_path))
    req = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DUMMY)
    job = provision(req)
    assert job.status == "done"
    assert job.root == tmp_path.resolve()
    assert is_complete(job.root)


def test_provision_dummy_skips_when_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TANTRA_DATA_DIR", str(tmp_path))
    req = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DUMMY)
    assert provision(req).status == "done"
    assert provision(req).status == "skipped"  # idempotent
    forced = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DUMMY, force=True)
    assert provision(forced).status == "done"


def test_provision_download_wired_delegates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TANTRA_DATA_DIR", str(tmp_path))
    req = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DOWNLOAD)
    # Download delegates to the tantra-data CLIs (network); assert the dispatch
    # reaches run_download and is NOT a NotImplementedError. run_download is
    # exercised end-to-end with monkeypatched CLIs in test_provision_download.py.
    monkeypatch.setattr(
        "tantra_examples.provision.run_download",
        lambda _req: ProvisionJob(
            job_id="dl-1",
            dataset=req.dataset,
            mode=req.mode,
            status="failed",
            root=tmp_path,
            error="delegated",
        ),
    )
    job = provision(req)
    assert job.status == "failed"
    assert job.error == "delegated"


def test_provision_monte_carlo_wired_now(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TANTRA_DATA_DIR", str(tmp_path))
    req = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.MONTE_CARLO, seed=7)
    job = provision(req)
    assert job.status == "done"
    assert is_complete(tmp_path)


def test_dummy_growth_symbol_rises_deterministically(tmp_path: Path) -> None:
    """RELIANCE grows at 0.2%/bar: the multibagger template's steady-growth leg."""
    days = sessions()
    closes_1 = [_close_probe("RELIANCE", i) for i in range(len(days))]
    # Exact reproducibility: the generator is a pure function of (symbol, index).
    closes_2 = [_close_probe("RELIANCE", i) for i in range(len(days))]
    assert closes_1 == closes_2
    assert closes_1[-1] > closes_1[0] * 3  # (1.002)^~1564 >> 3


def _close_probe(symbol: str, i: int) -> float:
    from tantra_examples.provision import dummy as _dummy

    return _dummy._close(symbol, i)
