"""backtesting/07_run_via_client: smoke test for the run-service client example.

The example degrades to a clear error at ``main()`` time (missing ``tantra.client``, or
``Client.inproc`` not available) instead of raising at import time; this test exercises
that degrade-gracefully contract (D7).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "examples" / "backtesting" / "07_run_via_client.py"


@pytest.fixture(scope="module")
def example():
    spec = importlib.util.spec_from_file_location("run_via_client", _PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_imports_cleanly(example):
    assert hasattr(example, "main")
    assert hasattr(example, "run_inproc")
    assert hasattr(example, "run_http")


def test_main_requires_data_dir(example):
    with pytest.raises(SystemExit):
        example.main([])


def test_main_reports_missing_client_surface(example, capsys):
    # --inproc keeps this deterministic: it never probes a live server on :8000. Whether the
    # wheel lacks tantra.client or ships it with Client.inproc unimplemented, exit 1 and name it.
    code = example.main(["--data-dir", ".", "--inproc"])
    assert code == 1
    err = capsys.readouterr().err
    assert "tantra.client" in err or "inproc" in err
