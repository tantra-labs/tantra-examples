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

from tantra_examples.provision.layout import catalog_dir, fundamentals_db, mutual_funds_db

SESSION_START = dt.date(2020, 1, 1)
SESSION_END = dt.date(2025, 12, 31)
FY_PERIODS = (dt.date(2022, 3, 31), dt.date(2024, 3, 31))
_IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

#: Evaluation date the mutual-fund screener resolves to (the last catalog session).
MF_STATS_ASOF = dt.date(2025, 12, 31)

#: Holdings disclosure date — 31 days before ``MF_STATS_ASOF``, comfortably inside
#: the screener's 10-day disclosure-lag window (no look-ahead).
MF_HOLDINGS_ASOF = dt.date(2025, 11, 30)

#: Synthetic scheme records: (scheme_code, scheme_name, category, plan, option, amc).
_MF_SCHEMES = (
    (
        "122639",
        "Quant Flexi Cap Fund - Direct Plan - Growth",
        "Equity:Flexi Cap",
        "Direct Plan",
        "Growth Option",
        "Quant Mutual Fund",
    ),
    (
        "125354",
        "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
        "Equity:Flexi Cap",
        "Direct Plan",
        "Growth Option",
        "PPFAS Mutual Fund",
    ),
    (
        "118989",
        "Axis ELSS Tax Saver Fund - Direct Plan - Growth",
        "Equity:ELSS",
        "Direct Plan",
        "Growth Option",
        "Axis Mutual Fund",
    ),
)

#: Synthetic fund stats: (scheme_code, nav, ter_pct, aum_cr, portfolio_turnover_pct).
_MF_STATS = (
    ("122639", "123.4500", "0.6500", "12500.0000", "41.0000"),
    ("125354", "456.7800", "0.6200", "8500.0000", "35.0000"),
    ("118989", "345.6000", "0.5200", "2100.0000", "25.0000"),
)

#: Per-company equity fundamentals for the lookthrough: (isin_code, market_cap_cr,
#: roce_pct, pe_ratio, debt_to_equity). Market caps span the large/mid/small bands
#: so the screener's cap-breakdown exercise sees all three buckets.
MF_COMPANY_FUNDAMENTALS: dict[str, tuple[str, str, str, str, str]] = {
    "RELIANCE": ("INE002A01018", "1500000.0", "18.0", "22.5", "0.4"),
    "TCS": ("INE467B01029", "1200000.0", "45.0", "28.0", "0.1"),
    "HDFCBANK": ("INE040A01034", "900000.0", "16.5", "19.0", "0.6"),
    "INFY": ("INE009A01021", "600000.0", "30.0", "25.0", "0.1"),
    "SBIN": ("INE062A01020", "400000.0", "10.0", "8.5", "1.0"),
    "ITC": ("INE154A01025", "200000.0", "35.0", "20.0", "0.2"),
    "LT": ("INE0BIN01018", "150000.0", "20.0", "30.0", "0.3"),
    "BHARTIARTL": ("INE397D01024", "4000.0", "12.0", "40.0", "0.5"),
}

#: Synthetic holdings per scheme: (isin, holding_name, weight_pct). A few weights
#: reference ISINs absent from ``companies`` so the lookthrough coverage is honest
#: (``coverage_pct < 100``) rather than silently complete.
_MF_HOLDINGS: dict[str, list[tuple[str, str, str]]] = {
    "122639": [
        ("INE002A01018", "Reliance Industries Ltd", "20.0"),
        ("INE467B01029", "Tata Consultancy Services Ltd", "15.0"),
        ("INE040A01034", "HDFC Bank Ltd", "12.0"),
        ("INE009A01021", "Infosys Ltd", "10.0"),
        ("INE062A01020", "State Bank of India", "9.0"),
        ("INE154A01025", "ITC Ltd", "8.0"),
        ("INE0BIN01018", "Larsen & Toubro Ltd", "6.0"),
        ("INE397D01024", "Bharti Airtel Ltd", "5.0"),
        ("IN00UNMATCHED1", "Unlisted Start-up", "8.0"),
        ("IN00UNMATCHED2", "Derivative Hedge", "7.0"),
    ],
    "125354": [
        ("INE002A01018", "Reliance Industries Ltd", "15.0"),
        ("INE467B01029", "Tata Consultancy Services Ltd", "12.0"),
        ("INE040A01034", "HDFC Bank Ltd", "10.0"),
        ("INE009A01021", "Infosys Ltd", "12.0"),
        ("INE062A01020", "State Bank of India", "8.0"),
        ("INE154A01025", "ITC Ltd", "10.0"),
        ("INE0BIN01018", "Larsen & Toubro Ltd", "8.0"),
        ("INE397D01024", "Bharti Airtel Ltd", "5.0"),
        ("IN00UNMATCHED3", "International Equity", "20.0"),
    ],
    "118989": [
        ("INE002A01018", "Reliance Industries Ltd", "25.0"),
        ("INE467B01029", "Tata Consultancy Services Ltd", "10.0"),
        ("INE040A01034", "HDFC Bank Ltd", "15.0"),
        ("INE009A01021", "Infosys Ltd", "15.0"),
        ("INE062A01020", "State Bank of India", "10.0"),
        ("INE154A01025", "ITC Ltd", "5.0"),
        ("INE0BIN01018", "Larsen & Toubro Ltd", "10.0"),
        ("INE397D01024", "Bharti Airtel Ltd", "5.0"),
        ("IN00UNMATCHED4", "Cash & Equivalents", "5.0"),
    ],
}

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


def write_symbol_parquet(
    path: Path, rows: list[tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal]]
) -> None:
    """Write one symbol parquet file with the wheel's decimal128(38, 10) schema (BIGINT ts)."""
    _write_parquet(path, rows)


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
    """Create ``<root>/fundamentals.duckdb`` with FY rows for both fiscal periods.

    ``companies`` carries the ``isin_code`` the mutual-fund lookthrough joins on
    (``mf_holdings.isin`` ↔ ``companies.isin_code``) plus the market-cap / ROCE /
    P/E / debt-to-equity columns the weighted portfolio math reads.
    """
    db_path = fundamentals_db(root)
    con = duckdb.connect(str(db_path))
    con.execute(
        "CREATE TABLE companies (symbol VARCHAR, company_name VARCHAR, isin_code VARCHAR, "
        "market_cap_cr DECIMAL(18,4), roce_pct DECIMAL(18,4), pe_ratio DECIMAL(18,4), "
        "debt_to_equity DECIMAL(18,4))"
    )
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
        isin_code, market_cap_cr, roce, pe_ratio, debt_to_equity = MF_COMPANY_FUNDAMENTALS[symbol]
        con.execute(
            "INSERT INTO companies VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                symbol,
                COMPANY_NAMES[symbol],
                isin_code,
                market_cap_cr,
                roce,
                pe_ratio,
                debt_to_equity,
            ],
        )
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


def build_mutual_funds(root: Path) -> None:
    """Write ``<root>/mutual_funds.duckdb`` (schemes, stats, holdings) for the screener.

    The synthetic mutual-fund store is written through the shipped
    ``tantra_data.store.mutual_funds.DuckDbMutualFundsStore`` (gap 0023 closed),
    so the provisioned file provably satisfies the screener's store surface
    (including the ``mf_fund_stats`` table the consumer reads directly).
    """
    from tantra_data.store.mutual_funds import DuckDbMutualFundsStore

    store = DuckDbMutualFundsStore(mutual_funds_db(root))
    for code, name, category, plan, option, amc in _MF_SCHEMES:
        store.put_scheme(code, name, category, plan, option, amc, MF_STATS_ASOF)
    for code, nav, ter, aum, turnover in _MF_STATS:
        store.put_fund_stats(code, MF_STATS_ASOF, nav, ter, aum, turnover)
    for code, holdings in _MF_HOLDINGS.items():
        store.put_holdings(code, MF_HOLDINGS_ASOF, holdings)


def build_lakehouse(root: Path) -> None:
    """Create the complete synthetic data lakehouse under ``root`` (idempotent).

    Builds only the missing pieces so a partially-provisioned root heals without
    clobbering the pieces that already exist.
    """
    if not catalog_dir(root).is_dir():
        build_catalog(root, sessions())
    if not fundamentals_db(root).is_file():
        build_fundamentals(root)
    if not mutual_funds_db(root).is_file():
        build_mutual_funds(root)


def is_complete(root: Path) -> bool:
    """True when the dummy layout already exists (catalog + fundamentals + mutual funds)."""
    return (
        catalog_dir(root).is_dir()
        and fundamentals_db(root).is_file()
        and mutual_funds_db(root).is_file()
    )


__all__ = [
    "COMPANY_NAMES",
    "FLAT_SPEC",
    "FY_PERIODS",
    "GROWTH_PER_BAR",
    "MF_COMPANY_FUNDAMENTALS",
    "MF_HOLDINGS_ASOF",
    "MF_STATS_ASOF",
    "SESSION_END",
    "SESSION_START",
    "build_catalog",
    "build_fundamentals",
    "build_lakehouse",
    "build_mutual_funds",
    "is_complete",
    "sessions",
    "write_symbol_parquet",
]
