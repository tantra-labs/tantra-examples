# mirror: kernel-verbatim port (gap 0003: tantra-data quantity query) —
# Decimal-canonical wheel retarget (ex 0006): quantities are exact ``Decimal``.

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

__all__ = ["Quantity", "QuantityError", "parse_quantity"]


class QuantityError(ValueError):
    """Raised when a quantity string cannot be parsed."""


@dataclass(frozen=True)
class Quantity:
    """Parsed quantity representing an evaluated numeric value and metadata.

    ``value`` and ``raw_number`` are exact ``Decimal`` (zero-floats policy).
    """

    value: Decimal
    raw_number: Decimal = Decimal(0)
    unit_suffix: str | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", Decimal(str(self.value)))
        object.__setattr__(self, "raw_number", Decimal(str(self.raw_number)))

    def __iter__(self) -> Iterator[Any]:
        return iter((self.value, self.unit_suffix or "shares"))

    def __getitem__(self, index: int) -> Any:
        return (self.value, self.unit_suffix or "shares")[index]


def parse_quantity(qty_str: str, market: str | None = None) -> Quantity:
    """Parse a quantity string into a Quantity object.

    Also unpacks as a tuple of (Decimal, unit) for backward compatibility.
    """
    qty_str = qty_str.strip()
    if not qty_str:
        raise QuantityError("empty quantity string")

    # Strip commas in numbers like 25,000 or 1,00,000
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", qty_str).lower()

    mult_map: dict[str, Decimal] = {
        "cr": Decimal(10_000_000),
        "crore": Decimal(10_000_000),
        "crores": Decimal(10_000_000),
        "lk": Decimal(100_000),
        "l": Decimal(100_000),
        "lakh": Decimal(100_000),
        "lakhs": Decimal(100_000),
        "k": Decimal(1_000),
        "thousand": Decimal(1_000),
        "m": Decimal(1_000_000),
        "mn": Decimal(1_000_000),
        "million": Decimal(1_000_000),
        "b": Decimal(1_000_000_000),
        "bn": Decimal(1_000_000_000),
        "billion": Decimal(1_000_000_000),
        "t": Decimal(1_000_000_000_000),
        "tn": Decimal(1_000_000_000_000),
        "trillion": Decimal(1_000_000_000_000),
        "%": Decimal("0.01"),
        "pct": Decimal("0.01"),
        "percent": Decimal("0.01"),
    }

    # Match numeric part and suffix
    m = re.match(r"^([\+\-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(.*)$", cleaned)
    if not m:
        raise QuantityError(f"invalid quantity string: {qty_str!r}")

    num_part, suffix_part = m.groups()
    try:
        raw_val = Decimal(num_part)
    except (ValueError, ArithmeticError) as exc:
        raise QuantityError(f"invalid number {num_part!r}") from exc

    suffix = suffix_part.strip()
    mult = Decimal(1)
    if suffix:
        if suffix in mult_map:
            mult = mult_map[suffix]
        else:
            raise QuantityError(f"unknown suffix {suffix!r}")

    final_val = raw_val * mult
    return Quantity(value=final_val, raw_number=raw_val, unit_suffix=suffix or "shares")
