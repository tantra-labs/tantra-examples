"""Deterministic synthetic NSE lakehouse for the offline screener/SIP tests.

The real ``tantra-data`` catalog checkout is absent from this workspace, so the
``_real_catalog``-gated tests build this stand-in once per session: a
``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet`` price catalog (2020-2025 weekday
bars with nanosecond 09:15 IST session stamps) plus ``<root>/fundamentals.duckdb``
with ``companies``, ``financial_ratios`` and ``financial_statements``. Pointing
``VYAAPAAR_DATA_DIR`` at ``<root>`` resolves every path the screeners use
(``find_catalog_path``, ``find_duckdb_path``).
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import duckdb

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


def _write_parquet(path: Path, rows: list[tuple[int, float, float, float, float, float]]) -> None:
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE b (ts BIGINT, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, "
        "volume DOUBLE)"
    )
    con.executemany("INSERT INTO b VALUES (?, ?, ?, ?, ?, ?)", rows)
    con.execute(f"COPY b TO '{path}' (FORMAT PARQUET)")
    con.close()


def build_catalog(root: Path, days: list[dt.date]) -> None:
    """Write ``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet`` for every symbol."""
    for symbol in COMPANY_NAMES:
        closes = [_close(symbol, i) for i in range(len(days))]
        by_year: dict[int, list[tuple[int, float, float, float, float, float]]] = {}
        prev = 100.0
        for i, (day, close) in enumerate(zip(days, closes, strict=True)):
            open_ = prev
            high = max(open_, close) * 1.01
            low = min(open_, close) * 0.99
            volume = 1_000_000.0 + i * 100.0
            by_year.setdefault(day.year, []).append(
                (_session_ts(day), open_, high, low, close, volume)
            )
            prev = close
        sym_dir = root / "catalog" / "1D" / "NSE" / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)
        for year, rows in sorted(by_year.items()):
            _write_parquet(sym_dir / f"{year}.parquet", rows)


def _fundamentals(symbol: str) -> dict[str, float]:
    # ITC pays a double-digit yield; every other symbol pays 4-6% (so the
    # strict min_div_yield=10.0 screen returns strictly fewer candidates).
    dividend = 2200.0 if symbol == "ITC" else 1000.0
    return {
        "eps": 12.0,
        "stockholders_equity": 12000.0,
        "shares": 200.0,
        "roce_pct": 18.0,
        "debt_to_equity": 0.4,
        "operating_margin_pct": 22.0,
        "free_cash_flow": 1500.0,
        "dividend": dividend,
    }


def build_fundamentals(root: Path) -> None:
    """Create ``<root>/fundamentals.duckdb`` with FY rows for both fiscal periods."""
    db_path = root / "fundamentals.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("CREATE TABLE companies (symbol VARCHAR, company_name VARCHAR)")
    con.execute(
        """CREATE TABLE financial_ratios (symbol VARCHAR, period_type VARCHAR, fiscal_date DATE,
        revenue DOUBLE, net_income DOUBLE, stockholders_equity DOUBLE, total_debt DOUBLE,
        operating_cash_flow DOUBLE, free_cash_flow DOUBLE, roce_pct DOUBLE, roe_pct DOUBLE,
        operating_margin_pct DOUBLE, net_margin_pct DOUBLE, debt_to_equity DOUBLE, eps DOUBLE)"""
    )
    con.execute(
        "CREATE TABLE financial_statements (symbol VARCHAR, period_type VARCHAR, "
        "statement_type VARCHAR, fiscal_date DATE, line_item VARCHAR, value DOUBLE, "
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
                    100_000.0,
                    2_400.0,
                    f["stockholders_equity"],
                    4_800.0,
                    1_800.0,
                    f["free_cash_flow"],
                    f["roce_pct"],
                    20.0,
                    f["operating_margin_pct"],
                    12.0,
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
    catalog = root / "catalog" / "1D" / "NSE"
    if catalog.is_dir() and (root / "fundamentals.duckdb").is_file():
        return
    build_catalog(root, sessions())
    build_fundamentals(root)
