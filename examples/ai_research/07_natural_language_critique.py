"""ai_research/07_natural_language_critique: design notes for an LLM backtest critique.

This is a runnable design-documentation script: it prints the Pitfalls prose below and runs a
tiny offline ``tantra.ai`` ask call to show the translation plumbing. The
``tantra.ai.verification.critic`` surface is future work (documented design) and is not imported.

Run::

    python examples/ai_research/07_natural_language_critique.py

Pitfalls::

    - A critique is not verification: a model can miss real bugs and flag non-issues. Every number
      it quotes must match a field of the structured BacktestResult, so require it to cite fields
      and check them in code.
    - Hindsight narrative: told the strategy and date range, a model can recall what the market
      did and "explain" the returns afterwards. Such explanations cannot be falsified, so use them
      to suggest tests to run, not as evidence.
    - Untrusted text in the prompt: strategy source, comments, symbol names and rationale strings
      are pasted into the critique prompt, so a comment saying "rate this excellent" is data, not an
      instruction. Validate the output against a structured Critique schema and never act on it
      automatically.
    - Critique-driven tweaking is a search: each edit made to satisfy the critic is another trial
      on the same data. Give the critic the out-of-sample and walk-forward results too, and keep a
      holdout it never sees.
    - Non-determinism: two runs give different critiques, and re-running until it approves is
      selection. Store the prompt, the response and a hash of the result it saw.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from tantra.ai.ask import translate_query
from tantra.ai.llm.provider import ScriptedFakeLlm

__all__ = ["FILTER", "QUERY", "main", "run"]

QUERY = "stocks with volume above 1m and an RSI below 30"
FILTER = "volume > 1000000 and rsi < 30"


def run() -> dict[str, Any]:
    """Tiny offline ask demo; the critic itself stays documented design."""
    llm = ScriptedFakeLlm(responses=[FILTER])
    result = translate_query(QUERY, llm)
    return {
        "ask_demo": {
            "query": QUERY,
            "filter_text": result.filter_text,
            "repair_count": result.repair_count,
        },
        "critic_status": (
            "tantra.ai.verification.critic is future work (documented design), not imported"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    print(__doc__)
    print(json.dumps(run(), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
