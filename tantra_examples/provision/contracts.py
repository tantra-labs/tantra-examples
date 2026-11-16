"""Provisioning request/job wire contract (plan 0004, milestone 1).

Pure dataclasses mirroring the illustrative ``POST /provision`` request and the
``GET /provision/jobs/{id}`` job status the service exposes. The library uses
them in-process; the HTTP layer (milestone 5) serializes them.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

from tantra_examples.provision.layout import Dataset, Mode

DEFAULT_START = dt.date(2020, 1, 1)
DEFAULT_END = dt.date(2025, 12, 31)
"""Default calendar window for generated series (matches the synthetic lakehouse)."""


@dataclass(frozen=True, slots=True)
class ProvisionRequest:
    """One ``/provision`` request: which dataset, mode, and parameters."""

    dataset: Dataset
    mode: Mode
    seed: int | None = None
    """``None`` → truly random Monte-Carlo; an ``int`` → reproducible run."""

    symbols: tuple[str, ...] = ()
    """Empty tuple → the default example universe (per-dataset)."""

    start: dt.date = DEFAULT_START
    end: dt.date = DEFAULT_END
    data_root: str | None = None
    """``None`` → ``$VYAAPAAR_DATA_DIR`` or the wheel's default data root."""

    force: bool = False
    """Re-provision an existing complete layout instead of skipping."""


@dataclass(frozen=True, slots=True)
class ProvisionJob:
    """Job status for one provisioning run (``GET /provision/jobs/{job_id}``)."""

    job_id: str
    dataset: Dataset
    mode: Mode
    status: str  # "running" | "done" | "failed" | "skipped"
    root: Path
    written: dict[str, int] = field(default_factory=dict)
    error: str | None = None


__all__ = [
    "DEFAULT_END",
    "DEFAULT_START",
    "ProvisionJob",
    "ProvisionRequest",
]
