"""Write a seeded/random Monte-Carlo 1D catalog and fundamentals DB (plan 0004, T15.3).

This provisioning mode writes the same canonical root layout as the dummy
mode:

* ``<root>/catalog/1D/NSE/<SYMBOL>/<year>.parquet`` with ``decimal128(38,10)``
  columns ``ts`` (BIGINT), ``open``, ``high``, ``low``, ``close``, ``volume``.
* ``<root>/fundamentals.duckdb`` with ``DECIMAL(18,4)`` tables via
  :func:`tantra_examples.provision.dummy.build_fundamentals`.

An integer ``seed`` makes runs byte-identical (research-live parity): the same
seed reproduces the exact same parquet bytes.  ``seed=None`` is entropy-seeded
through :mod:`random`, so it is truly random.  Fundamentals stay deterministic
(reused from the dummy mode); a fundamentals randomizer is a follow-on
refinement of plan 0004.
"""

from __future__ import annotations

import datetime as dt
import math
import random
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from tantra_examples.provision.contracts import ProvisionJob, ProvisionRequest
from tantra_examples.provision.dummy import (
    COMPANY_NAMES,
    _d,
    _session_ts,
    _write_parquet,
    build_fundamentals,
    is_complete,
    sessions,
)
from tantra_examples.provision.layout import (
    Dataset,
    catalog_dir,
    fundamentals_db,
    resolve_data_root,
)

_DT: Decimal = Decimal(1) / Decimal(252)
_QUANT: Decimal = Decimal("0.0000000001")


@dataclass(frozen=True)
class MonteCarloConfig:
    """Annual drift/vol GBM parameters for the generated close series."""

    drift: Decimal = Decimal("0.12")
    vol: Decimal = Decimal("0.25")
    base_price: Decimal = Decimal("1000.0")


def generate_closes(config: MonteCarloConfig, n: int, rng: random.Random) -> list[Decimal]:
    """Generate ``n`` GBM closes stepping on the log series.

    Each step is ``log_close += (drift - vol**2 / 2) * dt + vol * sqrt(dt) * z``
    with ``dt = 1/252`` and ``z ~ N(0, 1)`` drawn from ``rng``.  Float math is
    used only for the MC sampling; every returned value is an exact,
    quantized :class:`decimal.Decimal`.
    """

    log_close: Decimal = Decimal(0)
    closes: list[Decimal] = []
    drift_term: Decimal = config.drift - config.vol * config.vol / Decimal(2)
    vol_sqrt_dt: Decimal = config.vol * _DT.sqrt()
    for _ in range(n):
        z: Decimal = Decimal(str(rng.gauss(0.0, 1.0)))
        log_close += drift_term * _DT + vol_sqrt_dt * z
        exp_close: Decimal = Decimal(str(math.exp(float(log_close))))
        close: Decimal = (config.base_price * exp_close).quantize(_QUANT)
        closes.append(close)
    return closes


def provision_monte_carlo(request: ProvisionRequest) -> ProvisionJob:
    """Provision a Monte-Carlo catalog for ``request`` and return the job.

    Raises :class:`NotImplementedError` for datasets other than
    :attr:`Dataset.NSE_1D_CATALOG` and returns a ``"skipped"`` job when the
    root is already complete unless ``request.force`` is set.
    """

    root: Path = resolve_data_root(request.data_root)
    if request.dataset is not Dataset.NSE_1D_CATALOG:
        raise NotImplementedError("monte-carlo for this dataset is not wired yet (plan 0004)")
    if is_complete(root) and not request.force:
        return ProvisionJob(
            job_id="",
            dataset=request.dataset,
            mode=request.mode,
            status="skipped",
            root=root,
        )
    rng: random.Random = random.Random(request.seed)
    symbols: tuple[str, ...] = tuple(request.symbols) if request.symbols else tuple(COMPANY_NAMES)
    days: list[dt.date] = sessions()
    config: MonteCarloConfig = MonteCarloConfig()
    for symbol in symbols:
        closes: list[Decimal] = generate_closes(config, len(days), rng)
        symbol_dir: Path = catalog_dir(root) / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        by_year: dict[int, list[tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal]]] = {}
        prev_close: Decimal = config.base_price
        for i, day in enumerate(days):
            close: Decimal = closes[i]
            open_price: Decimal = prev_close
            high: Decimal = max(open_price, close) * Decimal("1.01")
            low: Decimal = min(open_price, close) * Decimal("0.99")
            volume: Decimal = _d(1_000_000.0 + i * 100.0)
            ts: int = _session_ts(day)
            row: tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal] = (
                ts,
                _d(float(open_price)),
                _d(float(high)),
                _d(float(low)),
                _d(float(close)),
                volume,
            )
            by_year.setdefault(day.year, []).append(row)
            prev_close = close
        for year, year_rows in sorted(by_year.items()):
            _write_parquet(symbol_dir / f"{year}.parquet", year_rows)
    # build_fundamentals is not idempotent (CREATE TABLE fails on re-run), so
    # only (re)build the deterministic fundamentals DB when it is missing.
    if not fundamentals_db(root).is_file():
        build_fundamentals(root)
    return ProvisionJob(
        job_id="",
        dataset=request.dataset,
        mode=request.mode,
        status="done",
        root=root,
        written={
            "catalog_symbols": len(symbols),
            "catalog_years": len({d.year for d in days}),
        },
    )


__all__ = ["MonteCarloConfig", "generate_closes", "provision_monte_carlo"]
