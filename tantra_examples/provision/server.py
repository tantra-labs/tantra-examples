"""HTTP microservice for the Tantra data-provisioning library (plan 0004, T15.5)."""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import threading
import uuid
from dataclasses import replace
from typing import Any

import fastapi
import uvicorn
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from tantra_examples.provision import provision
from tantra_examples.provision.contracts import ProvisionJob, ProvisionRequest
from tantra_examples.provision.layout import Dataset, Mode, resolve_data_root

__all__ = ["JobStore", "create_app", "job_to_dict", "serve"]


class JobStore:
    """Thread-safe in-memory store of provision jobs and cancellation flags."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, ProvisionJob] = {}
        self._cancel: dict[str, bool] = {}

    def put(self, job: ProvisionJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> ProvisionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: ProvisionJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def request_cancel(self, job_id: str) -> None:
        with self._lock:
            self._cancel[job_id] = True

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            return self._cancel.get(job_id, False)


def job_to_dict(job: ProvisionJob) -> dict[str, Any]:
    """Serialize a :class:`ProvisionJob` into a JSON-friendly mapping."""
    return {
        "job_id": job.job_id,
        "dataset": str(job.dataset),
        "mode": str(job.mode),
        "status": job.status,
        "root": str(job.root),
        "written": job.written,
        "error": job.error,
    }


def _failed_job(job_id: str, request: ProvisionRequest, error: str) -> ProvisionJob:
    """Build a failed :class:`ProvisionJob` for the given request."""
    return ProvisionJob(
        job_id=job_id,
        dataset=request.dataset,
        mode=request.mode,
        status="failed",
        root=resolve_data_root(request.data_root),
        error=error,
    )


def _run_job(store: JobStore, job_id: str, request: ProvisionRequest) -> None:
    """Execute a provision request in the background, keeping the store in sync."""
    store.update(
        ProvisionJob(
            job_id=job_id,
            dataset=request.dataset,
            mode=request.mode,
            status="running",
            root=resolve_data_root(request.data_root),
        )
    )
    if store.is_cancelled(job_id):
        store.update(_failed_job(job_id, request, "cancelled"))
        return
    try:
        result = provision(request)
    except Exception as exc:
        store.update(_failed_job(job_id, request, str(exc)))
        return
    if store.is_cancelled(job_id):
        store.update(_failed_job(job_id, request, "cancelled"))
    else:
        store.update(replace(result, job_id=job_id))


class ProvisionRequestIn(BaseModel):
    """HTTP request body for ``POST /provision``."""

    dataset: str
    mode: str
    seed: int | None = None
    symbols: list[str] = []
    start: dt.date = dt.date(2020, 1, 1)
    end: dt.date = dt.date(2025, 12, 31)
    data_root: str | None = None
    force: bool = False

    @field_validator("dataset")
    @classmethod
    def _normalize_dataset(cls, value: str) -> Dataset:
        try:
            return Dataset(value)
        except ValueError:
            raise ValueError(f"unknown dataset: {value}") from None

    @field_validator("mode")
    @classmethod
    def _normalize_mode(cls, value: str) -> Mode:
        try:
            return Mode(value)
        except ValueError:
            raise ValueError(f"unknown mode: {value}") from None


def create_app(store: JobStore | None = None) -> fastapi.FastAPI:
    """Build the FastAPI application exposing the provision HTTP endpoints."""
    if store is None:
        store = JobStore()
    app = fastapi.FastAPI(title="tantra-provision")
    app.state.store = store
    app.state.executor = concurrent.futures.ThreadPoolExecutor()

    @app.post("/provision")
    def create_provision_job(body: ProvisionRequestIn) -> JSONResponse:
        request = ProvisionRequest(
            dataset=Dataset(body.dataset),
            mode=Mode(body.mode),
            seed=body.seed,
            symbols=tuple(body.symbols),
            start=body.start,
            end=body.end,
            data_root=body.data_root,
            force=body.force,
        )
        job_id = uuid.uuid4().hex[:12]
        job = ProvisionJob(
            job_id=job_id,
            dataset=request.dataset,
            mode=request.mode,
            status="running",
            root=resolve_data_root(request.data_root),
        )
        store.put(job)
        app.state.executor.submit(_run_job, store, job_id, request)
        return JSONResponse(status_code=202, content=job_to_dict(job))

    @app.get("/provision/jobs/{job_id}")
    def get_provision_job(job_id: str) -> dict[str, Any]:
        job = store.get(job_id)
        if job is None:
            raise fastapi.HTTPException(status_code=404, detail="job not found")
        return job_to_dict(job)

    @app.post("/provision/jobs/{job_id}/cancel")
    def cancel_provision_job(job_id: str) -> dict[str, Any]:
        store.request_cancel(job_id)
        return {"job_id": job_id, "cancelled": True}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def serve(*, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the provision microservice with uvicorn."""
    uvicorn.run(create_app(), host=host, port=port)
