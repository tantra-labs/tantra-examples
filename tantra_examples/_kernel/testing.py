"""Deterministic harnesses for strategy tests.

``replay`` is the minimal bar replay: market intents fill at the close of their
respective instrument (or ``fill_delay`` bars later at the open), with no costs.
Sells fill before buys within each batch to prevent insufficient funds on rebalances.
``BarCloseFills`` is the simulated execution port of the conformance suite
(mirrors ``honba_sim::BarFillEngine``): it is re-exported from the shipped
``tantra.backtest.bar_close_fills`` (ex 0006 consolidation) instead of being
mirrored here. Use ``tantra.backtest`` for realistic simulation.

Decimal-canonical wheel retarget (ex 0006): every quantity and price is an exact
``decimal.Decimal`` on the shipped ``tantra.bar``/``tantra.order``/``tantra.trade``
types (zero-floats policy).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from tantra.backtest.bar_close_fills import BarCloseFills
from tantra.bar import Bar
from tantra.base import Strategy
from tantra.context import LedgerContext
from tantra.instrument import InstrumentId
from tantra.order import OrderIntent, OrderSide, OrderType
from tantra.tick import AggressorSide, QuoteTick, TradeTick
from tantra.trade import Trade

__all__ = ["BarCloseFills", "ReplayResult", "from_wire_messages", "replay"]


@dataclass
class _RestingTrailingStop:
    intent: OrderIntent
    peak: Decimal
    trough: Decimal


@dataclass
class ReplayResult:
    intents: list[OrderIntent] = field(default_factory=list)
    fills: list[Trade] = field(default_factory=list)


def replay(strategy: Strategy, bars: Iterable[Bar], fill_delay: int = 0) -> ReplayResult:
    """Replays ``bars``. ``fill_delay=0`` fills at the instrument's last close;
    ``fill_delay=n`` fills at the open of the bar ``n`` bars later, like a live runner.
    Within each fill batch, sells execute before buys so liquidation funds purchases.
    Trailing stops rest until breached, ratcheting stop price with peak/trough."""
    result = ReplayResult()
    queue: list[tuple[int, OrderIntent]] = []  # (due bar index, intent)
    resting_stops: list[_RestingTrailingStop] = []
    last_close: dict[InstrumentId, Decimal] = {}
    last_open: dict[InstrumentId, Decimal] = {}
    ids: dict[int, str] = {}  # id(intent) -> replay order id
    cancelled: set[str] = set()
    ledger = strategy.ctx if isinstance(strategy.ctx, LedgerContext) else None

    def settle(intent: OrderIntent, px: Decimal, ts: int) -> None:
        oid = ids[id(intent)]
        if oid in cancelled:
            return
        _fill(strategy, result, intent, px, ts, oid)
        if ledger is not None:
            ledger.note_closed(oid)
            apply_cancels()

    def apply_cancels() -> None:
        # Strategy cancel requests (OCO): the order never fills; the ledger releases it.
        nonlocal queue, resting_stops
        if ledger is None:
            return
        for oid in ledger.drain_cancels():
            intent = ledger.intent_of(oid)
            if intent is None or oid in cancelled:
                continue
            cancelled.add(oid)
            ledger.note_closed(oid)
            ledger.release(intent)
            queue = [q for q in queue if q[1] is not intent]
            resting_stops = [s for s in resting_stops if s.intent is not intent]

    strategy.on_start()
    for i, bar in enumerate(bars):
        last_close[bar.instrument_id] = bar.close
        last_open[bar.instrument_id] = bar.open
        if isinstance(strategy.ctx, LedgerContext):
            strategy.ctx.set_now(bar.ts)

        # Check resting trailing stops against this bar
        triggered: list[tuple[OrderIntent, Decimal]] = []
        remaining_stops: list[_RestingTrailingStop] = []
        for stop in resting_stops:
            if stop.intent.instrument_id != bar.instrument_id:
                remaining_stops.append(stop)
                continue
            if stop.intent.side is OrderSide.SELL:
                stop.peak = max(stop.peak, bar.high)
                if stop.intent.trail_amount is not None:
                    trigger_px = stop.peak - stop.intent.trail_amount
                else:
                    pct = (stop.intent.trail_percent or Decimal("0.0")) / Decimal("100.0")
                    trigger_px = stop.peak * (Decimal("1.0") - pct)
                if bar.low <= trigger_px:
                    fill_px = min(bar.open, trigger_px) if bar.open <= trigger_px else trigger_px
                    triggered.append((stop.intent, fill_px))
                else:
                    remaining_stops.append(stop)
            else:  # BUY
                stop.trough = min(stop.trough, bar.low)
                if stop.intent.trail_amount is not None:
                    trigger_px = stop.trough + stop.intent.trail_amount
                else:
                    pct = (stop.intent.trail_percent or Decimal("0.0")) / Decimal("100.0")
                    trigger_px = stop.trough * (Decimal("1.0") + pct)
                if bar.high >= trigger_px:
                    fill_px = max(bar.open, trigger_px) if bar.open >= trigger_px else trigger_px
                    triggered.append((stop.intent, fill_px))
                else:
                    remaining_stops.append(stop)
        resting_stops = remaining_stops

        triggered.sort(key=lambda item: 0 if item[0].side is OrderSide.SELL else 1)
        for intent, px in triggered:
            settle(intent, px, bar.ts)

        due = [q for q in queue if q[0] <= i]
        queue = [q for q in queue if q[0] > i]
        due.sort(key=lambda item: 0 if item[1].side is OrderSide.SELL else 1)
        for _, intent in due:
            px = last_open.get(intent.instrument_id, bar.open)
            settle(intent, px, bar.ts)
        strategy.on_bar(bar)
        apply_cancels()
        intents = strategy.drain_intents()
        for intent in intents:
            result.intents.append(intent)
            oid = f"replay-{len(result.intents) - 1}"
            ids[id(intent)] = oid
            if ledger is not None:
                ledger.note_order(oid, intent)
            if intent.order_type is OrderType.TRAILING_STOP:
                ref = bar.close
                resting_stops.append(_RestingTrailingStop(intent, peak=ref, trough=ref))
            elif fill_delay == 0:
                pass
            else:
                queue.append((i + fill_delay, intent))
        if fill_delay == 0:
            immediate = [it for it in intents if it.order_type is not OrderType.TRAILING_STOP]
            intents_to_fill = sorted(
                immediate, key=lambda it: 0 if it.side is OrderSide.SELL else 1
            )
            for intent in intents_to_fill:
                px = last_close.get(intent.instrument_id, bar.close)
                settle(intent, px, bar.ts)
    strategy.on_stop()
    return result


def _fill(
    strategy: Strategy,
    result: ReplayResult,
    intent: OrderIntent,
    price: Decimal,
    ts: int,
    order_id: str | None = None,
) -> None:
    fill = Trade(intent.instrument_id, intent.side, intent.quantity, price, ts, order_id)
    result.fills.append(fill)
    strategy.handle_fill(fill)


def from_wire_messages(
    payload: str | bytes,
) -> list[tuple[Bar | QuoteTick | TradeTick, int]]:
    """Parse a JSON list of wire ``Message``s into ``(domain event, ts_init)`` pairs.

    Parsed strictly (``tantra.entities.wire.loads_many``). Only market data (bar,
    quote, trade) is supported. The domain shapes keep the event time as ``ts``
    (integer nanoseconds, from the wire ``{iso, unix_nanos}`` object); the bar
    specification is dropped.
    """
    from tantra_examples._kernel.entities import wire  # unconverted sibling (ex 0006)

    out: list[tuple[Bar | QuoteTick | TradeTick, int]] = []
    for message in wire.loads_many("Message", payload):
        event = message.event
        domain: Bar | QuoteTick | TradeTick
        if isinstance(event, wire.BarEvent):
            domain = Bar(
                event.bar_type.instrument_id.to_domain(),
                event.ts_event.to_ns(),
                event.open,
                event.high,
                event.low,
                event.close,
                event.volume,
            )
        elif isinstance(event, wire.QuoteEvent):
            domain = QuoteTick(
                event.instrument_id.to_domain(),
                event.ts_event.to_ns(),
                event.bid_price,
                event.ask_price,
                event.bid_size,
                event.ask_size,
            )
        elif isinstance(event, wire.TradeEvent):
            domain = TradeTick(
                event.instrument_id.to_domain(),
                event.ts_event.to_ns(),
                event.price,
                event.size,
                AggressorSide(event.aggressor_side.value),
                event.trade_id,
            )
        else:
            raise ValueError(f"unsupported event type {event.type!r}; expected bar, quote or trade")
        out.append((domain, message.ts_init.to_ns()))
    return out
