"""Canonical deterministic dummy lakehouse (plan 0004 ``dummy`` mode).

The fold of the former test fixture ``tests/unit/synthetic_lakehouse.py``: one
canonical synthetic-data implementation for the whole workspace. Same values and
layout as the fixture, written DECIMAL-canonical (parquet decimal128(38,10)
matching ``tantra.store.BAR_SCHEMA``; duckdb DECIMAL columns) so every consumer
(sim, analyser, screeners, wheel store) reads exact ``Decimal`` values.

Idempotent: re-provisioning an existing complete root skips.
"""

from __future__ import annotations

import datetime as dt
import math
from decimal import Decimal
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from tantra_examples.provision.layout import catalog_dir, fundamentals_db

SESSION_START = dt.date(2020, 1, 1)
SESSION_END = dt.date(2025, 12, 31)
FY_PERIODS = (dt.date(2022, 3, 31), dt.date(2024, 3, 31))
_IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

COMPANY_NAMES: dict[str, str] = {
    "RELIANCE": "Reliance Industries Ltd",
    "TCS": "Tata Consultancy Services Ltd",
    "HDFCBANK": "HDFC Bank Ltd",
    "INFY": "Infosys Ltd",
    "SBIN": "State Bank of India",
    "ITC": "ITC Ltd",
    "LT": "Larsen & Toubro Ltd",
    "BHARTIARTL": "Bharti Airtel Ltd",
}

#: Steady-growth symbols: they clear the multibagger trend template as of
#: 2023-01-01 (1y return >= 15%) and stay far from their 52-week low later, so
#: they never leak into the value/dividend screens (52w-low proximity gate).
GROWTH_PER_BAR: dict[str, float] = {"RELIANCE": 0.002, "TCS": 0.0018}

#: Flat symbols: close sits within ~15% of the 52-week low for every asof the
#: tests use, so they pass the value/dividend proximity gate (and fail the
#: multibagger minimum-1y-return gate). Values are (amplitude, phase period).
FLAT_SPEC: dict[str, tuple[float, float]] = {
    "HDFCBANK": (2.0, 7.0),
    "INFY": (4.0, 5.0),
    "SBIN": (2.0, 11.0),
    "ITC": (3.0, 13.0),
    "LT": (2.0, 17.0),
    "BHARTIARTL": (2.5, 19.0),
}


def sessions() -> list[dt.date]:
    """All weekdays in ``[SESSION_START, SESSION_END]``, oldest first."""
    out: list[dt.date] = []
    day = SESSION_START
    while day <= SESSION_END:
        if day.weekday() < 5:
            out.append(day)
        day += dt.timedelta(days=1)
    return out


def _close(symbol: str, i: int) -> float:
    if symbol in GROWTH_PER_BAR:
        return 100.0 * (1.0 + GROWTH_PER_BAR[symbol]) ** i
    amp, period = FLAT_SPEC[symbol]
    return 100.0 + amp * math.sin(i / period)


def _session_ts(day: dt.date) -> int:
    stamp = dt.datetime(day.year, day.month, day.day, 9, 15, tzinfo=_IST)
    return int(stamp.timestamp() * 10**9)


def _write_parquet(
    path: Path, rows: list[tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal]]
) -> None:
    """Write one symbol-year partition with the wheel's decimal128(38, 10) schema."""
    table = pa.Table.from_arrays(
        [
            pa.array([r[0] for r in rows], type=pa.int64()),
            pa.array([r[1] for r in rows], type=pa.decimal128(38, 10)),
            pa.array([r[2] for r in rows], type=pa.decimal128(38, 10)),
            pa.array([r[3] for r in rows], type=pa.decimal128(38, 10)),
            pa.array([r[4] for r in rows], type=pa.decimal128(38, 10)),
            pa.array([r[5] for r in rows], type=pa.decimal128(38, 10)),
        ],
        schema=pa.schema(
            [
                ("ts", pa.int64()),
                ("open", pa.decimal128(38, 10)),
                ("high", pa.decimal128(38, 10)),
                ("low", pa.decimal128(38, 10)),
                ("close", pa.decimal128(38, 10)),
                ("volume", pa.decimal128(38, 10)),
            ]
        ),
    )
    pq.write_table(table, path, compression="snappy")


def _d(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0000000001"))


def build_catalog(root: Path, days: list[dt.date] | None = None) -> None:
    """Write ``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet`` for every symbol."""
    days = sessions() if days is None else days
    for symbol in COMPANY_NAMES:
        closes = [_close(symbol, i) for i in range(len(days))]
        by_year: dict[int, list[tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal]]] = {}
        prev = 100.0
        for i, (day, close) in enumerate(zip(days, closes, strict=True)):
            open_ = prev
            high = max(open_, close) * 1.01
            low = min(open_, close) * 0.99
            volume = 1_000_000.0 + i * 100.0
            by_year.setdefault(day.year, []).append(
                (
                    _session_ts(day),
                    _d(open_),
                    _d(high),
                    _d(low),
                    _d(close),
                    _d(volume),
                )
            )
            prev = close
        sym_dir = catalog_dir(root) / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)
        for year, rows in sorted(by_year.items()):
            _write_parquet(sym_dir / f"{year}.parquet", rows)


def _fundamentals(symbol: str) -> dict[str, Decimal]:
    # ITC pays a double-digit yield; every other symbol pays 4-6% (so the
    # strict min_div_yield=10.0 screen returns strictly fewer candidates).
    dividend = Decimal("2200.0") if symbol == "ITC" else Decimal("1000.0")
    return {
        "eps": _d(12.0),
        "stockholders_equity": _d(12000.0),
        "shares": _d(200.0),
        "roce_pct": _d(18.0),
        "debt_to_equity": _d(0.4),
        "operating_margin_pct": _d(22.0),
        "free_cash_flow": _d(1500.0),
        "dividend": dividend,
    }


def build_fundamentals(root: Path) -> None:
    """Create ``<root>/fundamentals.duckdb`` with FY rows for both fiscal periods."""
    db_path = fundamentals_db(root)
    con = duckdb.connect(str(db_path))
    con.execute("CREATE TABLE companies (symbol VARCHAR, company_name VARCHAR)")
    con.execute(
        """CREATE TABLE financial_ratios (symbol VARCHAR, period_type VARCHAR, fiscal_date DATE,
        revenue DECIMAL(18,4), net_income DECIMAL(18,4), stockholders_equity DECIMAL(18,4),
        total_debt DECIMAL(18,4), operating_cash_flow DECIMAL(18,4), free_cash_flow DECIMAL(18,4),
        roce_pct DECIMAL(18,4), roe_pct DECIMAL(18,4), operating_margin_pct DECIMAL(18,4),
        net_margin_pct DECIMAL(18,4), debt_to_equity DECIMAL(18,4), eps DECIMAL(18,4))"""
    )
    con.execute(
        "CREATE TABLE financial_statements (symbol VARCHAR, period_type VARCHAR, "
        "statement_type VARCHAR, fiscal_date DATE, line_item VARCHAR, value DECIMAL(18,4), "
        "currency VARCHAR)"
    )
    ratio_rows: list[tuple] = []
    stmt_rows: list[tuple] = []
    for symbol in COMPANY_NAMES:
        f = _fundamentals(symbol)
        con.execute("INSERT INTO companies VALUES (?, ?)", [symbol, COMPANY_NAMES[symbol]])
        for fiscal in FY_PERIODS:
            ratio_rows.append(
                (
                    symbol,
                    "FY",
                    fiscal.isoformat(),
                    Decimal("100000.0"),
                    Decimal("2400.0"),
                    f["stockholders_equity"],
                    Decimal("4800.0"),
                    Decimal("1800.0"),
                    f["free_cash_flow"],
                    f["roce_pct"],
                    _d(20.0),
                    f["operating_margin_pct"],
                    _d(12.0),
                    f["debt_to_equity"],
                    f["eps"],
                )
            )
            stmt_rows.append(
                (symbol, "FY", "x", fiscal.isoformat(), "Cash Dividends Paid", f["dividend"], "INR")
            )
            stmt_rows.append(
                (
                    symbol,
                    "FY",
                    "x",
                    fiscal.isoformat(),
                    "Diluted Average Shares",
                    f["shares"],
                    "INR",
                )
            )
    con.executemany(
        "INSERT INTO financial_ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ratio_rows,
    )
    con.executemany(
        "INSERT INTO financial_statements VALUES (?, ?, ?, ?, ?, ?, ?)",
        stmt_rows,
    )
    con.close()


def build_lakehouse(root: Path) -> None:
    """Create the complete synthetic data lakehouse under ``root`` (idempotent)."""
    catalog = catalog_dir(root)
    if catalog.is_dir() and fundamentals_db(root).is_file():
        return
    build_catalog(root, sessions())
    build_fundamentals(root)


def is_complete(root: Path) -> bool:
    """True when the dummy layout already exists (catalog + fundamentals)."""
    return catalog_dir(root).is_dir() and fundamentals_db(root).is_file()


__all__ = [
    "COMPANY_NAMES",
    "FLAT_SPEC",
    "FY_PERIODS",
    "GROWTH_PER_BAR",
    "SESSION_END",
    "SESSION_START",
    "build_catalog",
    "build_fundamentals",
    "build_lakehouse",
    "is_complete",
    "sessions",
]
