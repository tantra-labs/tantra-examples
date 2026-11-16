"""Synchronous download job runner for the data-provisioning service.

Download mode delegates to tantra-data's ingest CLIs (network + vendor
required). Provider failures surface as terminal ``"failed"`` jobs — never
silent empty data. The HTTP layer (milestone 5 of plan 0004) runs this
runner as a background job.
"""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

from tantra_examples.provision.contracts import ProvisionJob, ProvisionRequest
from tantra_examples.provision.dummy import COMPANY_NAMES
from tantra_examples.provision.layout import (
    Dataset,
    catalog_dir,
    fundamentals_db,
    mutual_funds_db,
    resolve_data_root,
)


class _CliModule(Protocol):
    """Structural type for the tantra-data ingest CLI entry points."""

    def main(self, argv: list[str]) -> int: ...


CLI_MODULE: dict[Dataset, str] = {
    Dataset.NSE_1D_CATALOG: "tantra_data.cli.ingest_catalog",
    Dataset.FUNDAMENTALS: "tantra_data.cli.ingest_fundamentals",
    Dataset.MUTUAL_FUNDS: "tantra_data.cli.ingest_mutual_funds",
}


def _build_argv(request: ProvisionRequest, root: Path) -> list[str]:
    """Build the argv for the owning tantra-data ingest CLI."""
    if request.dataset is Dataset.NSE_1D_CATALOG:
        return [
            "--catalog",
            str(catalog_dir(root)),
            "--start",
            request.start.isoformat(),
            "--end",
            request.end.isoformat(),
        ]
    if request.dataset is Dataset.FUNDAMENTALS:
        symbols = tuple(request.symbols) if request.symbols else tuple(COMPANY_NAMES)
        argv = ["--db", str(fundamentals_db(root))]
        for symbol in symbols:
            argv.extend(["--symbol", symbol])
        return argv
    if request.dataset is Dataset.MUTUAL_FUNDS:
        return ["--db", str(mutual_funds_db(root))]
    raise ValueError(f"download argv not wired for {request.dataset}")


def _job(
    request: ProvisionRequest,
    root: Path,
    *,
    status: str,
    error: str | None = None,
    written: dict[str, Any] | None = None,
) -> ProvisionJob:
    return ProvisionJob(
        job_id=f"download-{uuid.uuid4().hex[:8]}",
        dataset=request.dataset,
        mode=request.mode,
        status=status,
        root=root,
        written={} if written is None else written,
        error=error,
    )


def run_download(
    request: ProvisionRequest, *, cancel: Callable[[], bool] | None = None
) -> ProvisionJob:
    """Run a synchronous download, surfacing failures as ``"failed"`` jobs.

    The tantra-data ingest modules are imported lazily at call time so tests
    can monkeypatch their ``main`` entry points. A download cannot be
    interrupted mid-call in this synchronous runner; ``cancel`` is consulted
    only after the CLI returns.
    """
    root = resolve_data_root(request.data_root)
    if request.dataset not in CLI_MODULE:
        return _job(
            request,
            root,
            status="failed",
            error=f"download for {request.dataset} is not wired (plan 0004)",
        )
    module_name = CLI_MODULE[request.dataset]
    try:
        module = cast(_CliModule, importlib.import_module(module_name))
        argv = _build_argv(request, root)
        rc = module.main(argv)
    except Exception as exc:  # provider failures are terminal, never silent
        return _job(request, root, status="failed", error=str(exc))
    if cancel is not None and cancel():
        return _job(request, root, status="failed", error="cancelled")
    if rc != 0:
        return _job(
            request,
            root,
            status="failed",
            error=f"{module_name} exited with code {rc}",
        )
    return _job(request, root, status="done", written={"argv": argv})


__all__ = ["CLI_MODULE", "run_download"]
