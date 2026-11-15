"""ai_research/02_autoresearch_loop: deterministic demo of the autonomous research loop.

The full loop — hypothesis proposal, trial budget, deflated-Sharpe threshold, holdout, and a
seed-replay journal — is documented design (tantra-docs/docs/tutorials/autoresearch-loop.md);
``tantra.ai.autoresearch.*`` does not ship in the wheel. What this script runs is the offline,
deterministic core of that design: a ``ScriptedFakeLlm`` proposes hypotheses, each is translated
via ``tantra.ai.ask.translate_query`` into a validated screener filter, and the resulting order
decision is passed through ``tantra.ai.decision.guard_llm_decision`` (fail-closed, no quantity
increases, protective exits never shrunk).

Run::

    python examples/ai_research/02_autoresearch_loop.py

Pitfalls::

    - Multiple testing: every generated hypothesis is a trial, and the best of 100 looks good by
      chance. The design tracks num_trials_budget and a deflated Sharpe threshold; count every
      attempt, including ones the model or you discard, and report the trial count with the winner.
    - Data snooping through the journal: feeding earlier results back into the prompt (retrieved
      similar hypotheses, failures) lets the loop learn the test period. Keep a final holdout that
      never enters a prompt or the journal and touch it once.
    - LLM look-ahead: a model trained on data covering the backtest window can "propose" ideas it
      already knows worked. Prefer theory-first hypotheses, test windows after the model's
      training cutoff, and record the cutoff.
    - Non-determinism and cost: model output varies run to run. Store the prompt, the raw
      response and a seed so a result can be replayed, and cap iterations and spend.
    - Untrusted text: hypothesis text, journal entries and fetched documents are pasted into later
      prompts, so any of them can carry instructions. Generated strategy code must go through the
      verification sandbox, never be executed directly.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from tantra.ai.ask import translate_query
from tantra.ai.decision import guard_llm_decision
from tantra.ai.llm.provider import ScriptedFakeLlm
from tantra.instrument import InstrumentId
from tantra.order import OrderIntent

__all__ = ["HYPOTHESES", "main", "run"]

# (hypothesis, scripted filter the fake LLM replies with) — deterministic offline.
HYPOTHESES: list[tuple[str, str]] = [
    ("mean reversion: buy oversold large caps", "market_cap_basic > 100000000000 and rsi < 30"),
    ("momentum: strong-RSI leaders on volume", "rsi > 70 and volume > 500000"),
]


def run() -> dict[str, Any]:
    """One deterministic pass: translate each hypothesis and guard its order decision."""
    symbol = InstrumentId("NIFTY", "NSE")
    intent = OrderIntent.market_buy(symbol, 100.0)
    stop_loss = OrderIntent.stop_sell(symbol, 100.0, 95.0)

    results: list[dict[str, Any]] = []
    for name, filter_text in HYPOTHESES:
        llm = ScriptedFakeLlm(responses=[filter_text])
        translated = translate_query(name, llm)
        guard = guard_llm_decision(
            {
                "order_id": f"loop-{len(results)}",
                "decision": "approve",
                "decided_quantity": 100.0,
                "rationale": name,
            },
            intent,
        )
        results.append(
            {
                "hypothesis": name,
                "filter_text": translated.filter_text,
                "repair_count": translated.repair_count,
                "guard": {
                    "fail_closed": guard.fail_closed,
                    "overridden": guard.overridden,
                    "effective_quantity": (
                        None
                        if guard.effective_intent is None
                        else float(guard.effective_intent.quantity)
                    ),
                },
            }
        )

    # Protective-exit invariant: the model cannot cancel a stop-loss.
    exit_guard = guard_llm_decision(
        {"order_id": "loop-stop", "decision": "veto", "decided_quantity": 0.0}, stop_loss
    )

    return {
        "design": (
            "the full loop (trial budget, deflated-Sharpe threshold, holdout, seed-replay "
            "journal) is documented design; tantra.ai.autoresearch.* does not ship"
        ),
        "trials": len(results),
        "results": results,
        "protective_exit": {
            "model_decision": "veto",
            "overridden": exit_guard.overridden,
            "exit_kept": exit_guard.effective_intent == stop_loss,
        },
    }


def main(argv: list[str] | None = None) -> int:
    print(json.dumps(run(), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
