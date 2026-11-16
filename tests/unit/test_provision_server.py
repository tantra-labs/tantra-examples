"""Tests for the provision HTTP microservice and client (plan 0004, T15.5)."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient

from tantra_examples.provision.client import ProvisionClient
from tantra_examples.provision.contracts import ProvisionRequest
from tantra_examples.provision.layout import Dataset, Mode
from tantra_examples.provision.server import JobStore, create_app

DATA_DIR_ENV = "TANTRA_DATA_DIR"
TERMINAL_STATUSES = ("done", "skipped", "failed")
POLL_DEADLINE_S = 2.0
POLL_INTERVAL_S = 0.01


def _wait_terminal(fetch: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Poll ``fetch`` until the job reaches a terminal status."""
    deadline = time.monotonic() + POLL_DEADLINE_S
    job = fetch()
    while job["status"] not in TERMINAL_STATUSES and time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_S)
        job = fetch()
    return job


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_provision_dummy_returns_202_then_done(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    client = TestClient(create_app())
    response = client.post(
        "/provision",
        json={"dataset": "nse_1d_catalog", "mode": "dummy", "data_root": str(tmp_path)},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "running"
    job_id = body["job_id"]
    job = _wait_terminal(lambda: client.get(f"/provision/jobs/{job_id}").json())
    assert job["status"] == "done"
    assert job["root"] == str(tmp_path.resolve())


def test_invalid_mode_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    client = TestClient(create_app())
    response = client.post("/provision", json={"dataset": "nse_1d_catalog", "mode": "bogus"})
    assert response.status_code == 422


def test_unknown_job_is_404() -> None:
    client = TestClient(create_app())
    response = client.get("/provision/jobs/nope")
    assert response.status_code == 404
    assert response.json() == {"detail": "job not found"}


def test_job_store_cancel_flag() -> None:
    store = JobStore()
    store.request_cancel("x")
    assert store.is_cancelled("x") is True
    assert store.is_cancelled("other") is False


def test_cancel_marks_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    client = TestClient(create_app())
    response = client.post(
        "/provision",
        json={"dataset": "nse_1d_catalog", "mode": "dummy", "data_root": str(tmp_path)},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    cancel = client.post(f"/provision/jobs/{job_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json() == {"job_id": job_id, "cancelled": True}
    job = _wait_terminal(lambda: client.get(f"/provision/jobs/{job_id}").json())
    assert job["status"] in ("done", "failed")
    if job["status"] == "failed":
        assert "cancelled" in job["error"]


def test_client_hits_server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    with TestClient(create_app()) as http:
        provision_client = ProvisionClient("http://testserver")
        client = cast(httpx.Client, http)
        request = ProvisionRequest(
            dataset=Dataset.NSE_1D_CATALOG,
            mode=Mode.DUMMY,
            data_root=str(tmp_path),
        )
        body = provision_client.provision(request, client=client)
        assert body["status"] == "running"
        job_id = body["job_id"]
        job = _wait_terminal(lambda: provision_client.job(job_id, client=client))
        assert job["status"] in ("done", "skipped")
    print(f"client test job_id={job_id}")
