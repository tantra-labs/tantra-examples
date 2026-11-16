"""Provisioning library (plan 0004) — the canonical data-root provisioner.

The owning component for example-data provisioning: writes the
``$TANTRA_DATA_DIR`` layout (NSE 1D catalog + fundamentals.duckdb +
mutual_funds.duckdb) on request, in one of three modes:

* ``dummy`` — deterministic synthetic lakehouse (the fold of the old
  ``tests/unit/synthetic_lakehouse.py`` fixture: one canonical synthetic source);
* ``monte-carlo`` — seeded-or-truly-random GBM series (milestone 3);
* ``download`` — delegates to the tantra-data ingest CLIs (milestone 4).

The HTTP microservice (milestones 5-6) is a thin job layer over this library.
"""

from __future__ import annotations

from tantra_examples.provision.contracts import (
    DEFAULT_END,
    DEFAULT_START,
    ProvisionJob,
    ProvisionRequest,
)
from tantra_examples.provision.download import run_download
from tantra_examples.provision.dummy import (
    COMPANY_NAMES,
    build_catalog,
    build_fundamentals,
    build_lakehouse,
    is_complete,
    sessions,
    write_symbol_parquet,
)
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
from tantra_examples.provision.monte_carlo import (
    MonteCarloConfig,
    provision_monte_carlo,
)

__version__ = "0.1.0"


def provision(request: ProvisionRequest) -> ProvisionJob:
    """Provision a data root per ``request``.

    ``dummy``, ``monte-carlo`` and ``download`` are implemented; ``download``
    delegates to the tantra-data ingest CLIs and is network-dependent.
    """
    root = resolve_data_root(request.data_root)
    if request.mode is Mode.DOWNLOAD:
        return run_download(request)
    if request.mode is Mode.MONTE_CARLO:
        return provision_monte_carlo(request)
    if request.mode is not Mode.DUMMY:
        raise ValueError(f"unknown mode: {request.mode}")
    if request.dataset not in (Dataset.NSE_1D_CATALOG, Dataset.FUNDAMENTALS):
        raise NotImplementedError(
            "mutual_funds dummy needs tantra-data gap 0023 store surface "
            "(see tantra-data/docs/gaps/0023-mutual-funds-store-surface.md)"
        )
    if is_complete(root) and not request.force:
        return ProvisionJob(
            job_id="",
            dataset=request.dataset,
            mode=request.mode,
            status="skipped",
            root=root,
        )
    build_lakehouse(root)
    written = {
        "catalog_symbols": len(COMPANY_NAMES),
        "catalog_years": len({day.year for day in sessions()}),
    }
    return ProvisionJob(
        job_id="",
        dataset=request.dataset,
        mode=request.mode,
        status="done",
        root=root,
        written=written,
    )


__all__ = [
    "COMPANY_NAMES",
    "DATA_DIR_ENV",
    "DEFAULT_END",
    "DEFAULT_START",
    "Dataset",
    "Mode",
    "MonteCarloConfig",
    "ProvisionJob",
    "ProvisionRequest",
    "build_catalog",
    "build_fundamentals",
    "build_lakehouse",
    "catalog_dir",
    "fundamentals_db",
    "is_complete",
    "mutual_funds_db",
    "provision",
    "provision_monte_carlo",
    "resolve_data_root",
    "run_download",
    "sessions",
    "symbol_year_path",
    "write_symbol_parquet",
]
