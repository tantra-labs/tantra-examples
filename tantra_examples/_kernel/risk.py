"""Pre-trade risk for Python (ADR 0018).

A thin face on the Rust risk gate: the types are the native ones
(``_kernel.native``), so the rules, their order and the numbers they report are
identical to the Rust engine and to the shared golden vectors. The engine
behind them is ``tantra-risk``, the authoritative gate (SEBI algo ids, the
order-to-trade ratio breaker, price bands, freeze limits, kill switches).
Importing this module does not need the extension; the first attribute access
does (see :mod:`_kernel.native`).

* :class:`RiskLimits`: per-run limits (``max_notional``, ``order_rate``);
  :meth:`RiskLimits.from_dict` is the one parser of the ``[risk]`` config
  table (unknown keys are refused).
* :class:`RiskEngine`: the gate itself — ``check_order(order)`` raises
  :class:`RiskRefusalError` when the gate refuses an order.
* :class:`RiskStage`: ``check(order)`` answers with a :class:`RiskDecision`
  (``approved``, ``code``, ``rule``, ``context``) instead of raising.
* :class:`TradingState`: ``ACTIVE`` / ``REDUCING`` / ``HALTED``; ``str()`` is the wire spelling.
* :class:`Command`: the operator command a live shell accepts — ``Command.stop()`` and
  ``Command.state(TradingState.REDUCING)``.
* :func:`limits_from_config`: reads ``[risk]`` from a run's parsed TOML table.
"""
# mirror: kernel-verbatim port (gap 0006) — Decimal-canonical wheel retarget (ex 0006)

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from tantra_examples._kernel.native import native_attr

__all__ = [
    "Command",  # noqa: F822 - lazy, see __getattr__
    "OrderRejected",
    "RiskDecision",  # noqa: F822 - lazy, see __getattr__
    "RiskEngine",  # noqa: F822 - lazy, see __getattr__
    "RiskLimits",  # noqa: F822 - lazy, see __getattr__
    "RiskRefusal",
    "RiskRefused",
    "RiskStage",  # noqa: F822 - lazy, see __getattr__
    "TradingState",  # noqa: F822 - lazy, see __getattr__
    "check_order",
    "limits_from_config",
]

_NATIVE = frozenset(
    {
        "Command",
        "RiskDecision",
        "RiskEngine",
        "RiskLimits",
        "RiskStage",
        "TradingState",
    }
)

_POSITION_EPS = Decimal("1e-9")
"""Tolerance for the reduce-only rule (legacy float-sourced positions were exact
decimal in the Rust gate itself)."""


def __getattr__(name: str) -> Any:
    if name in _NATIVE:
        return native_attr(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def limits_from_config(config: Mapping[str, Any]) -> Any:
    """The :class:`RiskLimits` of a run's parsed TOML table.

    Reads the ``[risk]`` table (and ``[risk.order_rate]``) through
    :meth:`RiskLimits.from_dict`, the same parser the Rust config uses; an
    absent section means no limits. Raises ``ValueError`` for an unknown key
    or an invalid value.

    Return type is ``Any``: :class:`RiskLimits` only exists as a dynamic
    ``native_attr`` proxy (gap 0006), not a statically importable name.
    """
    table = config.get("risk")
    return native_attr("RiskLimits").from_dict({} if table is None else dict(table))


def check_order(order: Any, now: Any = None) -> None:
    """Check one order against the gate.

    Raises :class:`_kernel.native.RiskRefusalError` when the gate refuses the
    order; the exception carries the stable rule code (``sebi_otr_breach``,
    ``price_band_violation``, ...) and the refusal as JSON.
    """
    engine = native_attr("RiskEngine")()
    engine.register_algo(getattr(order, "algo_id", ""))
    engine.check_order(order, now)


@dataclass(frozen=True, slots=True)
class RiskRefusal:
    """A refused order, in the audit-record shape the runner writes.

    The live refusal raised by the gate is ``_kernel.native.RiskRefusalError``;
    this record is what the audit trail keeps.
    """

    code: str
    rule: str
    context: dict[str, Any] = field(default_factory=dict)


def check_state(
    side: Any, quantity: Decimal, position: Decimal, trading_state: Any
) -> RiskRefusal | None:
    """The trading-state rules: ``Halted`` refuses everything, ``Reducing`` refuses
    anything that would open the position further.

    ``position`` is the signed position plus the same-side working remainder.
    While ``Reducing`` an order passes only if ``position + sign * quantity``
    stays within ``[min(position, 0), max(position, 0)]`` (a flat position
    refuses everything). Quantities and positions are exact ``Decimal``;
    the small tolerance below absorbs legacy float-sourced positions during the
    transition, while the gate itself (``_kernel.native.RiskEngine``) is exact
    decimal.
    """
    state = str(trading_state)
    if state == "halted":
        return RiskRefusal("risk_trading_halted", "trading_halted", {"rule": "trading_halted"})
    if state != "reducing":
        return None
    sign = Decimal("1") if str(getattr(side, "value", side)).upper() == "BUY" else Decimal("-1")
    qty = Decimal(str(quantity))
    pos = Decimal(str(position))
    after = pos + sign * qty
    if (
        abs(pos) > _POSITION_EPS
        and after >= min(pos, Decimal("0")) - _POSITION_EPS
        and after <= max(pos, Decimal("0")) + _POSITION_EPS
    ):
        return None
    return RiskRefusal(
        "risk_reduce_only_violation",
        "reduce_only",
        {
            "rule": "reduce_only",
            "position": pos,
            "side": getattr(side, "value", side),
            "quantity": qty,
        },
    )


@dataclass(frozen=True, slots=True)
class RiskRefused:
    """Audit record: the risk gate refused ``order_id`` at ``ts`` (ns). Always followed by
    the :class:`OrderRejected` for the same order (``AuditKind::RiskRefused``)."""

    order_id: str
    ts: int
    code: str
    rule: str
    context: dict[str, Any]


@dataclass(frozen=True, slots=True)
class OrderRejected:
    """Audit record: ``order_id`` was refused before submit; ``reason`` is the ``ErrorCode``
    wire spelling (``AuditKind::OrderRejected``)."""

    order_id: str
    ts: int
    reason: str
