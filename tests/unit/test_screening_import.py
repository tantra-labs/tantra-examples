"""`import tantra_examples.screening` must work without the optional tantra-data extra."""

from __future__ import annotations

import importlib

import pytest


def test_screening_package_imports_without_tantra_data() -> None:
    mod = importlib.import_module("tantra_examples.screening")
    assert callable(mod.screen_mutual_funds)


def test_screen_mutual_funds_reports_missing_extra_clearly() -> None:
    try:
        import tantra_data  # noqa: F401
    except ModuleNotFoundError:
        from tantra_examples.screening import screen_mutual_funds

        with pytest.raises(ModuleNotFoundError, match="mutual-funds"):
            screen_mutual_funds()
    else:
        pytest.skip("tantra_data installed; missing-extra path not reachable")
