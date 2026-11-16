#!/usr/bin/env python3
"""basic/06_paper_trading: a seeded PaperSession round trip on the compiled engine.

Runs the native paper-exchange engine (``tantra-exec-paper`` through the
``tantra.paper`` wheel surface, ``tantra-ffi`` plan 0003) in fully deterministic
seeded mode: a limit buy rests, a market sell crosses it, and the fills, cash
and equity are printed. ``seed=`` selects the engine's seeded latency model, so
the same seed reproduces the same tape byte for byte. No broker credentials
required - the engine is offline and exact-decimal throughout.

Run::

    python examples/basic/06_paper_trading.py
    python examples/basic/06_paper_trading.py --out paper.json
    python examples/basic/06_paper_trading.py --seed 42

Pitfalls::

    - Determinism is per seed: a different seed changes the latency draws (and so
      the exact ready timestamps), but the fills still land on the next advance.
      Compare runs with the SAME seed (the tests do).
    - A market order with no contra liquidity is rejected by the engine
      (``NoMarketPrice``): place resting liquidity before the crossing order.
    - This is a paper engine, not a broker: fills are simulated, there is no
      settlement, and positions are derived from fills (nothing is seeded).
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from tantra.instrument import InstrumentId
from tantra.paper import PaperSession


def serialize_fill(fill: Any) -> dict[str, Any]:
    return {
        "fill_id": fill.fill_id,
        "order_id": fill.order_id,
        "instrument": fill.instrument.to_str(),
        "side": str(fill.side),
        "price": str(fill.price),
        "quantity": str(fill.quantity),
        "timestamp": fill.timestamp,
    }


def run(seed: int = 7, cash: str = "1000000") -> dict[str, Any]:
    """A deterministic paper round trip: resting limit buy, crossing market sell."""
    session = PaperSession(cash=Decimal(cash), seed=seed)
    reliance = InstrumentId("RELIANCE", "NSE")
    session.set_market_price(reliance, Decimal("100"))
    buy_id = session.place_order(
        reliance, "BUY", Decimal("10"), order_type="LIMIT", limit_price=Decimal("100")
    )
    sell_id = session.place_order(reliance, "SELL", Decimal("10"), order_type="MARKET")
    session.advance_to("2023-11-14T22:14:00Z")

    return {
        "seed": seed,
        "orders": {"limit_buy": buy_id, "market_sell": sell_id},
        "fills": [serialize_fill(f) for f in session.fills()],
        "equity": str(session.equity()),
        "cash": str(session.cash()),
        "positions": {str(k): str(v) for k, v in session.positions().items()},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic seeded paper-trading session and print fills + equity."
    )
    parser.add_argument("--seed", default=7, type=int, help="Latency RNG seed (default: 7).")
    parser.add_argument("--cash", default="1000000", help="Initial cash (default: 1000000).")
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to write the JSON result to.",
    )

    args = parser.parse_args(argv)
    result = run(seed=args.seed, cash=args.cash)
    text = json.dumps(result, indent=2, default=str) + "\n"
    if args.out:
        Path(args.out).write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
