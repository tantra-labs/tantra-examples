"""Compatibility helpers for the examples harness.

The ``tantra`` native wheel and the sibling SDK/data packages are optional at
runtime; pure-Python ``decimal.Decimal`` fallbacks keep every example
deterministic and offline-runnable.
"""

from __future__ import annotations

from decimal import Decimal

try:  # pragma: no cover - exercised only when the native wheel is absent
    from tantra import Decimal as TantraDecimal

    VYAAPAAR_AVAILABLE = True
except ImportError:  # pragma: no cover
    TantraDecimal = Decimal
    VYAAPAAR_AVAILABLE = False

D = Decimal
