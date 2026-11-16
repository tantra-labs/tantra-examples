"""tests/unit/test_09_alpha30_cross_sectional: Alpha 30 cross-sectional factor model."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest
from tantra.coverage import DateInterval
from tantra.instrument import InstrumentId
from tantra.store import ParquetBarStore, find_data_root

from tantra_examples.base import REPO_ROOT
from tantra_examples.provision.dummy import write_symbol_parquet

_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "universes" / "09_alpha30_cross_sectional.py"
)


@pytest.fixture(scope="module")
def example():
    spec = importlib.util.spec_from_file_location("alpha30_cross_sectional", _PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def _default_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Build a deterministic synthetic 1D NSE catalog for ``main()``'s store run.

    Replaces the skip (the real ``tantra-data`` lakehouse is absent here) with a
    synthetic lakehouse under ``tmp_path``: ``$TANTRA_DATA_DIR`` points the
    store's data root there, so the same ``main()`` invocation reads the synthetic
    parquet at ``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet``.
    """
    root = tmp_path / "data_root"
    symbols = ["RELIANCE", "HINDALCO", "SAIL", "VEDL", "ASHOKLEY", "BHEL", "NATIONALUM"]
    _write_lakehouse_catalog(root, symbols, dt.date(2023, 1, 2), dt.date(2024, 12, 31))
    monkeypatch.setenv("TANTRA_DATA_DIR", str(root))
    store = ParquetBarStore(find_data_root(REPO_ROOT))
    interval = DateInterval(dt.date(2023, 1, 2), dt.date(2024, 12, 31) + dt.timedelta(days=1))
    bars = store.read(InstrumentId("RELIANCE", "NSE"), "1D", interval)
    assert bars, "synthetic RELIANCE.NSE catalog must yield bars"


def _d(v: float) -> Decimal:
    """Exact decimal conversion (zero floats in financial values)."""
    return Decimal(str(v)).quantize(Decimal("0.0000000001"))


def _ts(day: dt.date) -> int:
    """Epoch-ns for the 09:15 session-open bar (golden lakehouse timestamp)."""
    return int(dt.datetime.combine(day, dt.time(9, 15), tzinfo=dt.UTC).timestamp()) * 1_000_000_000


def _write_symbol_parquet(
    nse_dir: Path,
    symbol: str,
    closes: list[float],
    days: list[dt.date],
    *,
    year: int = 2024,
) -> None:
    """Fold onto the canonical provisioner writer (decimal128, plan 0004)."""
    rows = [
        (
            _ts(day),
            _d(close),
            _d(close + 0.5),
            _d(close - 0.5),
            _d(close),
            Decimal("1000000.0"),
        )
        for day, close in zip(days, closes, strict=True)
    ]
    (nse_dir / symbol).mkdir(parents=True, exist_ok=True)
    write_symbol_parquet(nse_dir / symbol / f"{year}.parquet", rows)


def _synthetic_catalog(tmp_path: Path, symbols: list[str], asof: dt.date) -> Path:
    """``<tmp>/catalog/1D/NSE/<SYMBOL>/2024.parquet`` with bars rising through ``asof``."""
    nse_dir = tmp_path / "catalog" / "1D" / "NSE"
    days: list[dt.date] = []
    d = dt.date(2024, 1, 2)
    while d <= asof:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    assert len(days) >= 100, f"only {len(days)} sessions before {asof}"
    for i, symbol in enumerate(symbols):
        drift = 0.0004 * (i + 1)  # distinct personalities so factor ranking is meaningful
        closes = [100.0 * (1.0 + drift) ** j for j in range(len(days))]
        _write_symbol_parquet(nse_dir, symbol, closes, days)
    return nse_dir


def _write_lakehouse_catalog(root: Path, symbols: list[str], start: dt.date, end: dt.date) -> Path:
    """Write ``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet`` for every year in the
    window, each symbol with a distinct deterministic drift so the cross-sectional
    factor ranking is meaningful."""
    nse_dir = root / "catalog" / "1D" / "NSE"
    days: list[dt.date] = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    assert len(days) >= 200, f"only {len(days)} sessions in {start}..{end}"
    for i, symbol in enumerate(symbols):
        drift = 0.0004 * (i + 1)  # distinct personalities so factor ranking is meaningful
        closes = [100.0 * (1.0 + drift) ** j for j in range(len(days))]
        for year in range(start.year, end.year + 1):
            year_days = [day for day in days if day.year == year]
            year_closes = [c for day, c in zip(days, closes, strict=True) if day.year == year]
            _write_symbol_parquet(nse_dir, symbol, year_closes, year_days, year=year)
    return nse_dir


def test_run_shape_and_summary(example, tmp_path: Path) -> None:
    nse_dir = _synthetic_catalog(tmp_path, ["AAA", "BBB", "CCC", "DDD"], dt.date(2024, 9, 30))
    result = example.run(
        catalog_dir=str(nse_dir),
        symbols=["AAA", "BBB", "CCC", "DDD"],
        start_date=dt.date(2024, 4, 1),
        end_date=dt.date(2024, 9, 30),
        initial_capital=1_000_000.0,
        top_decile=0.5,
        min_history_bars=5,
        fee=0.001,
    )
    assert set(result) >= {"config", "factors", "rebalances", "trades", "summary"}
    assert result["config"]["n_symbols"] == 4
    assert result["config"]["top_decile"] == 0.5
    assert result["summary"]["n_rebalances"] >= 1  # every 21 sessions
    summary = result["summary"]
    for key in (
        "final_equity",
        "total_return_pct",
        "cagr_pct",
        "sharpe",
        "max_drawdown_pct",
        "n_rebalances",
        "n_trades",
        "turnover",
    ):
        assert key in summary
    assert summary["n_trades"] >= 1


def test_top_decile_selection_and_rebalance_cadence(example, tmp_path: Path) -> None:
    nse_dir = _synthetic_catalog(tmp_path, ["AAA", "BBB", "CCC", "DDD"], dt.date(2024, 9, 30))
    result = example.run(
        catalog_dir=str(nse_dir),
        symbols=["AAA", "BBB", "CCC", "DDD"],
        start_date=dt.date(2024, 4, 1),
        end_date=dt.date(2024, 9, 30),
        top_decile=0.25,
        min_history_bars=5,
    )
    max_n = max(1, round(4 * 0.25))
    for rb in result["rebalances"]:
        assert 1 <= rb["n_selected"] <= max_n
        assert set(rb["selection"]) <= {"AAA", "BBB", "CCC", "DDD"}
        assert rb["trades"] >= 0
    dates = [rb["date"] for rb in result["rebalances"]]
    assert dates == sorted(dates)


def test_run_is_deterministic(example, tmp_path: Path) -> None:
    nse_dir = _synthetic_catalog(tmp_path, ["AAA", "BBB", "CCC"], dt.date(2024, 9, 30))
    kwargs = {
        "catalog_dir": str(nse_dir),
        "symbols": ["AAA", "BBB", "CCC"],
        "start_date": dt.date(2024, 5, 1),
        "end_date": dt.date(2024, 9, 30),
        "top_decile": 0.5,
        "min_history_bars": 5,
    }
    first = json.dumps(example.run(**kwargs), sort_keys=True, default=str)
    second = json.dumps(example.run(**kwargs), sort_keys=True, default=str)
    assert first == second


def test_empty_catalog_returns_flat_curve(example, tmp_path: Path) -> None:
    nse_dir = tmp_path / "1D" / "NSE"
    nse_dir.mkdir(parents=True)
    result = example.run(
        catalog_dir=str(nse_dir),
        symbols=["NOPE"],
        start_date=dt.date(2024, 4, 1),
        end_date=dt.date(2024, 9, 30),
    )
    assert result["rebalances"] == []
    assert result["trades"] == []
    assert result["summary"]["final_equity"] == 1_000_000.0


def test_main_writes_run_json_against_real_store(
    example, tmp_path, capsys, _default_catalog
) -> None:
    example.main(
        [
            "--start",
            "2023-01-02",
            "--end",
            "2024-12-31",
            "--out-dir",
            str(tmp_path / "out"),
            "--top-decile",
            "0.2",
        ]
    )
    run_json = tmp_path / "out" / "run.json"
    assert run_json.is_file()
    data = json.loads(run_json.read_text())
    assert data["run_hash"]
    assert data["config"]["top_decile"] == 0.2
    assert data["config"]["universe_name"] == "nifty50"
    assert 1 <= data["data_coverage"]["n_with_data"] <= 30
    assert data["result"]["n_rebalances"] >= 1
    out_text = capsys.readouterr().out
    assert "Alpha-30 cross-sectional" in out_text or "run_hash" in out_text
