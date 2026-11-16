"""`import tantra_examples.screening` must work without the optional tantra-data extra."""

from __future__ import annotations

import importlib
import sys

import pytest


def test_screening_package_imports_without_tantra_data() -> None:
    mod = importlib.import_module("tantra_examples.screening")
    assert callable(mod.screen_mutual_funds)


class _BlockTantraData:
    """``sys.meta_path`` finder that makes ``tantra_data`` imports raise ModuleNotFoundError.

    Simulates the optional ``tantra-data`` extra being absent so the degradation
    path is exercised even when the package is installed in the environment.
    """

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname == "tantra_data" or fullname.startswith("tantra_data."):
            raise ModuleNotFoundError(f"No module named '{fullname}'")
        return None


def test_screen_mutual_funds_reports_missing_extra_clearly(monkeypatch) -> None:
    from tantra_examples.screening import screen_mutual_funds

    monkeypatch.setattr(sys, "meta_path", [_BlockTantraData(), *sys.meta_path])
    with pytest.raises(ModuleNotFoundError, match="tantra-data"):
        screen_mutual_funds()
