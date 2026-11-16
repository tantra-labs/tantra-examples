"""Unit tests for tantra_examples.provision.download (plan 0004, T15.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tantra_examples.provision.contracts import ProvisionRequest
from tantra_examples.provision.download import run_download
from tantra_examples.provision.layout import (
    Dataset,
    Mode,
    catalog_dir,
    fundamentals_db,
    mutual_funds_db,
)


@pytest.fixture(autouse=True)
def _set_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every test at an isolated TANTRA_DATA_DIR."""
    monkeypatch.setenv("TANTRA_DATA_DIR", str(tmp_path))


def test_catalog_argv_and_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        seen.append(argv)
        return 0

    monkeypatch.setattr("tantra_data.cli.ingest_catalog.main", fake_main)

    job = run_download(ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DOWNLOAD))

    assert job.status == "done"
    assert job.written == {"argv": seen[0]}
    argv = seen[0]
    assert argv[argv.index("--catalog") + 1] == str(catalog_dir(tmp_path))
    assert argv[argv.index("--start") + 1] == "2020-01-01"
    assert argv[argv.index("--end") + 1] == "2025-12-31"


def test_catalog_failure_is_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tantra_data.cli.ingest_catalog.main", lambda argv: 1)

    job = run_download(ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DOWNLOAD))

    assert job.status == "failed"
    assert job.error is not None
    assert "exited with code 1" in job.error


def test_fundamentals_argv_uses_symbols(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        seen.append(argv)
        return 0

    monkeypatch.setattr("tantra_data.cli.ingest_fundamentals.main", fake_main)

    job = run_download(ProvisionRequest(dataset=Dataset.FUNDAMENTALS, mode=Mode.DOWNLOAD))

    assert job.status == "done"
    argv = seen[0]
    assert argv[0] == "--db"
    assert argv[1] == str(fundamentals_db(tmp_path))
    assert argv[argv.index("--symbol") + 1] == "RELIANCE"


def test_mutual_funds_argv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        seen.append(argv)
        return 0

    monkeypatch.setattr("tantra_data.cli.ingest_mutual_funds.main", fake_main)

    job = run_download(ProvisionRequest(dataset=Dataset.MUTUAL_FUNDS, mode=Mode.DOWNLOAD))

    assert job.status == "done"
    assert seen[0] == ["--db", str(mutual_funds_db(tmp_path))]


def test_unsupported_dataset_is_terminal_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tantra_examples.provision.download.CLI_MODULE", {})

    job = run_download(ProvisionRequest(dataset=Dataset.MUTUAL_FUNDS, mode=Mode.DOWNLOAD))

    assert job.status == "failed"
    assert job.error is not None
    assert "not wired" in job.error


def test_exception_surfaces_as_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(argv: list[str]) -> int:
        raise RuntimeError("vendor down")

    monkeypatch.setattr("tantra_data.cli.ingest_catalog.main", boom)

    job = run_download(ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DOWNLOAD))

    assert job.status == "failed"
    assert job.error is not None
    assert "vendor down" in job.error


def test_cancel_flag_after_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tantra_data.cli.ingest_catalog.main", lambda argv: 0)

    job = run_download(
        ProvisionRequest(dataset=Dataset.NSE_1D_CATALOG, mode=Mode.DOWNLOAD),
        cancel=lambda: True,
    )

    assert job.status == "failed"
    assert job.error is not None
    assert "cancelled" in job.error
