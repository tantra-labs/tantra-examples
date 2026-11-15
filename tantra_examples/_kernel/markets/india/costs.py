"""NSE / BSE cash-equity and F&O transaction costs (India).

Pure functions — no I/O, no wall clock.  The backtest simulator and live
broker adapters call these to populate ``Trade.costs``; ``LedgerContext``
already debits the field on every fill.

Rates reflect the discount-broker (Zerodha-style) schedule in force for
equity *delivery* (CNC) in the 2025-26 financial year.  Intraday and F&O
schedules are included so a single module covers the whole Indian stack.

References
----------
- Zerodha Brokerage Calculator / charges schedule
- NSE circulars on transaction charges, IPFT, STT
- Stamp duty (Maharashtra / central schedule for delivery)
"""
# mirror: kernel-verbatim port (gap 0004) — Decimal-canonical wheel retarget (ex 0006)

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum, auto

from tantra.money import Currency, Money
from tantra.order import OrderSide


# ---------------------------------------------------------------------------
# Segment / product
# ---------------------------------------------------------------------------
class Segment(Enum):
    EQUITY_DELIVERY = auto()  # CNC
    EQUITY_INTRADAY = auto()  # MIS / intraday
    FNO_FUTURES = auto()
    FNO_OPTIONS = auto()


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    """Itemised costs for one fill (settlement currency = INR)."""

    brokerage: Decimal
    stt: Decimal
    exchange: Decimal
    sebi: Decimal
    ipft: Decimal
    stamp_duty: Decimal
    gst: Decimal

    @property
    def total(self) -> Decimal:
        return (
            self.brokerage
            + self.stt
            + self.exchange
            + self.sebi
            + self.ipft
            + self.stamp_duty
            + self.gst
        )


# ---------------------------------------------------------------------------
# Rate tables (2025-26)
# ---------------------------------------------------------------------------
# Equity delivery (CNC)
_EQ_DEL_STT_SELL = Decimal("0.0010")  # 0.10 % on sell
_EQ_DEL_STAMP_BUY = Decimal("0.00015")  # 0.015 % on buy
_EQ_DEL_EXCH = Decimal("0.0000297")  # NSE transaction charge
_EQ_DEL_SEBI = Decimal("0.000001")  # ₹10 / crore
_EQ_DEL_IPFT = Decimal("0.000001")  # approx
_EQ_DEL_BROKERAGE_PCT = Decimal("0.0003")  # 0.03 %
_EQ_DEL_BROKERAGE_CAP = Decimal("20.0")  # ₹20 per order

# Equity intraday (MIS)
_EQ_INT_STT_SELL = Decimal("0.00025")  # 0.025 % on sell
_EQ_INT_STAMP_BUY = Decimal("0.00003")  # 0.003 % on buy
_EQ_INT_EXCH = Decimal("0.0000297")
_EQ_INT_SEBI = Decimal("0.000001")
_EQ_INT_IPFT = Decimal("0.000001")
_EQ_INT_BROKERAGE_PCT = Decimal("0.0003")
_EQ_INT_BROKERAGE_CAP = Decimal("20.0")

_GST_RATE = Decimal("0.18")

# CostBreakdown field order (same as the dataclass declaration).
_COST_FIELDS = ("brokerage", "stt", "exchange", "sebi", "ipft", "stamp_duty", "gst")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def nse_equity_delivery_cost(
    side: OrderSide,
    quantity: Decimal,
    price: Decimal,
) -> Decimal:
    """Total transaction cost (INR) for one NSE equity *delivery* fill.

    Parameters
    ----------
    side:
        ``OrderSide.BUY`` or ``OrderSide.SELL``.
    quantity:
        Absolute share quantity (positive).
    price:
        Fill price in INR.

    Returns
    -------
    Decimal
        Total cost in INR (always ≥ 0).
    """
    return nse_equity_delivery_breakdown(side, quantity, price).total


def nse_equity_delivery_breakdown(
    side: OrderSide,
    quantity: Decimal,
    price: Decimal,
) -> CostBreakdown:
    """Itemised NSE equity delivery costs (each leg shown to 4 decimals)."""
    return _rounded(_delivery_legs(side, quantity, price))


def _is_buy(side: OrderSide) -> bool:
    return side is OrderSide.BUY or str(side).upper().endswith("BUY")


def _delivery_legs(side: OrderSide, quantity: Decimal, price: Decimal) -> CostBreakdown:
    """Unrounded delivery legs; GST is on the unrounded taxable legs."""
    notional = abs(quantity * price)
    if notional <= 0:
        return CostBreakdown(
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        )
    is_buy = _is_buy(side)
    brokerage = min(_EQ_DEL_BROKERAGE_PCT * notional, _EQ_DEL_BROKERAGE_CAP)
    exchange = _EQ_DEL_EXCH * notional
    sebi = _EQ_DEL_SEBI * notional
    ipft = _EQ_DEL_IPFT * notional
    return CostBreakdown(
        brokerage=brokerage,
        stt=Decimal("0") if is_buy else _EQ_DEL_STT_SELL * notional,
        exchange=exchange,
        sebi=sebi,
        ipft=ipft,
        stamp_duty=_EQ_DEL_STAMP_BUY * notional if is_buy else Decimal("0"),
        gst=_GST_RATE * (brokerage + exchange + sebi + ipft),
    )


def _rounded(legs: CostBreakdown) -> CostBreakdown:
    return CostBreakdown(
        *(
            getattr(legs, name).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            for name in _COST_FIELDS
        )
    )


def nse_equity_intraday_cost(
    side: OrderSide,
    quantity: Decimal,
    price: Decimal,
) -> Decimal:
    """Total cost for one NSE equity *intraday* (MIS) fill."""
    return nse_equity_intraday_breakdown(side, quantity, price).total


def nse_equity_intraday_breakdown(
    side: OrderSide,
    quantity: Decimal,
    price: Decimal,
) -> CostBreakdown:
    """Itemised NSE equity intraday costs (each leg shown to 4 decimals)."""
    return _rounded(_intraday_legs(side, quantity, price))


def _intraday_legs(side: OrderSide, quantity: Decimal, price: Decimal) -> CostBreakdown:
    """Unrounded intraday legs; GST is on the unrounded taxable legs."""
    notional = abs(quantity * price)
    if notional <= 0:
        return CostBreakdown(
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        )
    is_buy = _is_buy(side)
    brokerage = min(_EQ_INT_BROKERAGE_PCT * notional, _EQ_INT_BROKERAGE_CAP)
    exchange = _EQ_INT_EXCH * notional
    sebi = _EQ_INT_SEBI * notional
    ipft = _EQ_INT_IPFT * notional
    return CostBreakdown(
        brokerage=brokerage,
        stt=Decimal("0") if is_buy else _EQ_INT_STT_SELL * notional,
        exchange=exchange,
        sebi=sebi,
        ipft=ipft,
        stamp_duty=_EQ_INT_STAMP_BUY * notional if is_buy else Decimal("0"),
        gst=_GST_RATE * (brokerage + exchange + sebi + ipft),
    )


def cost_for_segment(
    segment: Segment,
    side: OrderSide,
    quantity: Decimal,
    price: Decimal,
) -> Decimal:
    """Dispatch to the correct schedule by segment."""
    if segment is Segment.EQUITY_DELIVERY:
        return nse_equity_delivery_cost(side, quantity, price)
    if segment is Segment.EQUITY_INTRADAY:
        return nse_equity_intraday_cost(side, quantity, price)
    # F&O schedules can be added later; return 0 for now so callers don't break
    return Decimal("0")


def _fill_cost_money(legs: CostBreakdown) -> Money:
    # Unrounded legs; each is rounded to paise once here, then summed (ADR 0011):
    # a total a contract note can show.
    total = Money.zero(Currency.INR)
    for leg in (
        legs.brokerage,
        legs.stt,
        legs.exchange,
        legs.sebi,
        legs.ipft,
        legs.stamp_duty,
        legs.gst,
    ):
        total = total + Money.from_major(leg, Currency.INR)
    return total


def nse_equity_delivery_fill_cost(side: OrderSide, quantity: Decimal, price: Decimal) -> Money:
    """NSE equity delivery (CNC) cost of one fill as INR ``Money``, each leg rounded once.

    The ``(side, quantity, price) -> Money`` shape is the simulator's fill-cost function
    (``_kernel.backtest.simulated.FillCostFn``).
    """
    return _fill_cost_money(_delivery_legs(side, quantity, price))


def nse_equity_intraday_fill_cost(side: OrderSide, quantity: Decimal, price: Decimal) -> Money:
    """NSE equity intraday (MIS) cost of one fill as INR ``Money``, each leg rounded once."""
    return _fill_cost_money(_intraday_legs(side, quantity, price))
