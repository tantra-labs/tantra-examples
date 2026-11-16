"""Plan 0004 seam wiring: screener CLIs offer download / dummy / monte-carlo when the
catalog is absent (the per-example runtime prompt), and the data-root env var is
``TANTRA_DATA_DIR`` (renamed from ``VYAAPAAR_DATA_DIR``).

Covers:
* the missing-catalog error message naming the real ``--data-dir`` flag and env var;
* non-interactive (piped) runs stopping cleanly instead of hanging on a prompt;
* the interactive dummy provision path building the catalog and running the screen;
* provisioning failures surfacing as a terminal error;
* ``--data-dir`` accepting either a data root or the catalog directory itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tantra_examples.provision import Mode
from tantra_examples.screener_cli import ScreenerCLIExample
from tantra_examples.screening import find_catalog_path


class _StubScreener(ScreenerCLIExample):
    """Minimal concrete screener: no data dependencies beyond the catalog dir."""

    def screen(self, catalog_dir: Path, asof) -> list:
        return []

    def render_table(self, candidates, asof) -> None:
        return None


class _Stdin:
    """Fake stdin so the interactive TTY check is deterministic."""

    def __init__(self, isatty: bool) -> None:
        self._isatty = isatty

    def isatty(self) -> bool:
        return self._isatty


@pytest.fixture
def no_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Run from a scratch cwd with no data root discoverable anywhere."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TANTRA_DATA_DIR", raising=False)
    monkeypatch.delenv("VYAAPAAR_DATA_DIR", raising=False)
    return tmp_path


def test_missing_catalog_message_names_real_flag_and_env(no_data: Path) -> None:
    with pytest.raises(FileNotFoundError) as exc:
        find_catalog_path()
    msg = str(exc.value)
    assert "--catalog-dir" not in msg, msg
    assert "--data-dir" in msg, msg
    assert "TANTRA_DATA_DIR" in msg, msg


def test_non_tty_missing_catalog_returns_one_and_prints_guidance(
    no_data: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(sys, "stdin", _Stdin(isatty=False))
    ex = _StubScreener()
    assert ex.run() == 1
    err = capsys.readouterr().err
    assert "TANTRA_DATA_DIR" in err
    assert "--data-dir" in err
    assert "--catalog-dir" not in err


def test_provisioning_failure_returns_one(
    no_data: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(sys, "stdin", _Stdin(isatty=True))
    monkeypatch.setenv("TANTRA_DATA_DIR", str(no_data / "data"))

    def _boom(*args, **kwargs):
        raise RuntimeError("vendor down")

    monkeypatch.setattr("tantra_examples.provision.seam.ensure_data_root", _boom)
    ex = _StubScreener()
    assert ex.run() == 1
    assert "vendor down" in capsys.readouterr().err


def test_interactive_dummy_provision_builds_catalog_and_runs(
    no_data: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(sys, "stdin", _Stdin(isatty=True))
    root = no_data / "data"
    monkeypatch.setenv("TANTRA_DATA_DIR", str(root))
    # The interactive prompt answers "dummy" without touching real stdin.
    monkeypatch.setattr("tantra_examples.provision.seam.choose_mode", lambda: Mode.DUMMY)

    ex = _StubScreener()
    assert ex.run() == 0
    assert (root / "catalog" / "1D" / "NSE").is_dir()
    assert (root / "fundamentals.duckdb").is_file()
    err = capsys.readouterr().err
    assert "provisioned (dummy done)" in err


def test_data_dir_accepts_data_root_or_catalog_dir(no_data: Path) -> None:
    root = no_data / "data"
    catalog = root / "catalog" / "1D" / "NSE"
    catalog.mkdir(parents=True)

    ex = _StubScreener()
    ex.data_dir = root  # a data root: <root>/catalog/1D/NSE is resolved underneath it
    assert ex.resolve_catalog_dir() == catalog.resolve()

    ex.data_dir = catalog  # the catalog dir itself
    assert ex.resolve_catalog_dir() == catalog.resolve()
