"""Seam tests for interactive data-root provisioning (plan 0004 T15.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tantra_examples.provision.dummy import build_lakehouse, is_complete
from tantra_examples.provision.layout import Mode
from tantra_examples.provision.seam import ensure_data_root

DATA_DIR_ENV = "TANTRA_DATA_DIR"


def test_dummy_chooser_provisions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty root provisioned with the dummy mode ends complete."""
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    job = ensure_data_root(chooser=lambda: Mode.DUMMY)
    assert job.status == "done"
    assert is_complete(tmp_path)


def test_complete_root_is_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A complete root is skipped without calling ``provision``."""
    build_lakehouse(tmp_path)
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))

    def _explode(*args: object, **kwargs: object) -> object:
        raise AssertionError("provision must not run for a complete root")

    monkeypatch.setattr("tantra_examples.provision.seam.provision", _explode)
    job = ensure_data_root()
    assert job.status == "skipped"
    assert job.mode is Mode.DUMMY


def test_monte_carlo_surfaces_milestone_3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A not-yet-wired mode fails with its milestone pointer, never silent empty data."""

    def _not_wired(_req: object) -> object:
        raise NotImplementedError("monte-carlo mode is not wired yet (milestone 3)")

    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    monkeypatch.setattr("tantra_examples.provision.seam.provision", _not_wired)
    job = ensure_data_root(chooser=lambda: Mode.MONTE_CARLO)
    assert job.status == "failed"
    assert "milestone 3" in (job.error or "")


def test_download_surfaces_milestone_4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The download mode fails with its milestone pointer (not yet wired)."""

    def _not_wired(_req: object) -> object:
        raise NotImplementedError("download mode is not wired yet (milestone 4)")

    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    monkeypatch.setattr("tantra_examples.provision.seam.provision", _not_wired)
    job = ensure_data_root(chooser=lambda: Mode.DOWNLOAD)
    assert job.status == "failed"
    assert "milestone 4" in (job.error or "")
