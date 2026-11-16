"""Thin HTTP client for the provision microservice (plan 0004, T15.5)."""

from __future__ import annotations

from typing import Any

import httpx

from tantra_examples.provision.contracts import ProvisionRequest

__all__ = ["ProvisionClient"]


class ProvisionClient:
    """Minimal HTTP client for the provision microservice."""

    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    def provision(
        self, request: ProvisionRequest, client: httpx.Client | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset": request.dataset.value,
            "mode": request.mode.value,
            "seed": request.seed,
            "symbols": list(request.symbols),
            "start": request.start.isoformat(),
            "end": request.end.isoformat(),
            "data_root": request.data_root,
            "force": request.force,
        }
        url = f"{self._base}/provision"
        if client is not None:
            response = client.post(url, json=payload)
        else:
            response = httpx.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def job(self, job_id: str, client: httpx.Client | None = None) -> dict[str, Any]:
        url = f"{self._base}/provision/jobs/{job_id}"
        response = client.get(url) if client is not None else httpx.get(url)
        response.raise_for_status()
        return response.json()

    def cancel(self, job_id: str, client: httpx.Client | None = None) -> dict[str, Any]:
        url = f"{self._base}/provision/jobs/{job_id}/cancel"
        response = client.post(url) if client is not None else httpx.post(url)
        response.raise_for_status()
        return response.json()
