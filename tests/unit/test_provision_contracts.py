"""Unit: provisioning request/job wire contract (plan 0004, milestone 1)."""

from __future__ import annotations

from pathlib import Path

from tantra_examples.provision.contracts import (
    DEFAULT_END,
    DEFAULT_START,
    ProvisionJob,
    ProvisionRequest,
)
from tantra_examples.provision.layout import Dataset, Mode


def test_provision_request_defaults() -> None:
    req = ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DUMMY)
    assert req.seed is None
    assert req.symbols == ()
    assert req.start == DEFAULT_START
    assert req.end == DEFAULT_END
    assert req.data_root is None
    assert req.force is False


def test_provision_request_seeded_monte_carlo() -> None:
    req = ProvisionRequest(
        dataset=Dataset.NSE_1D_CATALOG,
        mode=Mode.MONTE_CARLO,
        seed=42,
        symbols=("RELIANCE", "TCS"),
    )
    assert req.seed == 42
    assert req.symbols == ("RELIANCE", "TCS")
    assert req.mode is Mode.MONTE_CARLO


def test_provision_job_fields() -> None:
    job = ProvisionJob(
        job_id="job-1",
        dataset=Dataset.FUNDAMENTALS,
        mode=Mode.DUMMY,
        status="done",
        root=Path("/tmp/root"),
        written={"companies": 8},
    )
    assert job.job_id == "job-1"
    assert job.status == "done"
    assert job.root == Path("/tmp/root")
    assert job.written == {"companies": 8}


def test_provision_job_error_carries_message() -> None:
    job = ProvisionJob(
        job_id="job-2",
        dataset=Dataset.NSE_1D_CATALOG,
        mode=Mode.DOWNLOAD,
        status="failed",
        root=Path("/tmp/root"),
        error="vendor down",
    )
    assert job.error == "vendor down"
