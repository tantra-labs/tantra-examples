"""Compatibility shim for the canonical synthetic lakehouse (plan 0004).

The deterministic synthetic NSE lakehouse now lives in the provisioning
library — ``tantra_examples.provision.dummy`` (the fold of this former fixture)
— so there is exactly one synthetic-data implementation for the whole workspace.
This module re-exports it under the old name so existing test fixtures
(``tests/unit/conftest.py``) keep working unchanged; new code should import from
``tantra_examples.provision``.
"""

from __future__ import annotations

from tantra_examples.provision.dummy import (  # noqa: F401
    COMPANY_NAMES,
    FLAT_SPEC,
    FY_PERIODS,
    GROWTH_PER_BAR,
    SESSION_END,
    SESSION_START,
    build_catalog,
    build_fundamentals,
    build_lakehouse,
    sessions,
)
