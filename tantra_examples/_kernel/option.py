"""Option domain models (ADR 0014).

Option contracts, chains, styles and kinds for derivative pricing and execution.

Decimal-canonical (ex 0006): every price, strike, implied volatility and size is an
exact ``decimal.Decimal``; ``InstrumentId`` is the wheel's ``tantra.instrument`` type.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from tantra.instrument import InstrumentId
from tantra.types import to_decimal

__all__ = ["OptionChain", "OptionContract", "OptionKind", "OptionStyle"]

# Financial fields that must be finite and non-negative Decimals.
_FINANCIAL_FIELDS = ("strike", "bid", "ask", "mid", "iv", "open_interest", "volume")


class OptionKind(Enum):
    """Call or Put option."""

    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    """Exercise style: European or American."""

    EUROPEAN = "european"
    AMERICAN = "american"


@dataclass(frozen=True, slots=True)
class OptionContract:
    """A single option contract."""

    instrument_id: InstrumentId
    expiry: dt.date
    strike: Decimal
    kind: OptionKind
    style: OptionStyle = OptionStyle.EUROPEAN
    bid: Decimal = Decimal(0)
    ask: Decimal = Decimal(0)
    mid: Decimal = Decimal(0)
    iv: Decimal = Decimal(0)
    open_interest: Decimal = Decimal(0)
    volume: Decimal = Decimal(0)
    greeks: Any = None

    def __post_init__(self) -> None:
        for name in _FINANCIAL_FIELDS:
            value = to_decimal(getattr(self, name))
            if not value.is_finite() or value < 0:
                raise ValueError(f"{name} must be finite and >= 0, got {value}")
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class OptionChain:
    """A snapshot of options across strikes and expiries for an underlying."""

    underlying: InstrumentId
    expiry: dt.date
    spot: Decimal
    contracts: list[OptionContract]

    def __post_init__(self) -> None:
        spot = to_decimal(self.spot)
        if not spot.is_finite() or spot < 0:
            raise ValueError(f"spot must be finite and >= 0, got {spot}")
        object.__setattr__(self, "spot", spot)
