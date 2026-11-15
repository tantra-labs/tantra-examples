"""ai_research/04_nl_to_strategy: natural language to strategy (filter) translation demo.

The full pipeline — generated strategy code through the static, sandbox and lookahead
verification modules — is documented design: ``tantra.ai.verification.*`` does not ship in the
wheel. What this script runs is the offline, deterministic first step of that pipeline: a
natural-language description is translated via ``tantra.ai.ask.translate_query`` (with a
``ScriptedFakeLlm``) into a validated screener filter against the ``tantra.screener`` catalog.

Run::

    python examples/ai_research/04_nl_to_strategy.py

Pitfalls::

    - Generated code is untrusted: run it only after the parser and AST checks and inside the
      sandbox in tantra.ai.verification, never with exec in the host process, and allow no
      imports, file or network access.
    - Hallucinated names: a model invents indicators, fields and tickers that do not exist.
      Resolve every identifier against the catalog and the instrument list and fail on a miss
      rather than substituting a default.
    - Vague language becomes parameters: "strong momentum" turns into a lookback the model picked.
      Regenerating until the backtest passes is a parameter search, so count each generation as a
      trial and test the final one on data it never saw.
    - Look-ahead written by the model: same-bar close fills, shifted indicators and hard-coded
      winners. The model may know which stocks did well in the stated window, so flag literal
      symbol lists and check the lookahead report, not the author's intent.
    - Non-determinism: the same description yields different code each time. Hash the generated
      source and store the prompt so a result can be tied to the exact code that ran.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from tantra.ai.ask import translate_query
from tantra.ai.llm.provider import ScriptedFakeLlm
from tantra.screener import load_catalog

__all__ = ["FILTER", "QUERY", "main", "run"]

QUERY = "large cap stocks with an RSI below 30"
FILTER = "market_cap_basic > 100000000000 and rsi < 30"


def run() -> dict[str, Any]:
    """Translate one natural-language description into a validated screener filter."""
    catalog = load_catalog()
    llm = ScriptedFakeLlm(responses=[FILTER])
    result = translate_query(QUERY, llm, catalog=catalog)
    return {
        "query": QUERY,
        "filter_text": result.filter_text,
        "repair_count": result.repair_count,
        "raw_responses": result.raw_responses,
        "catalog": {
            "metric_count": sum(1 for _ in catalog),
            "sample_keys": [m.key for m in list(catalog)[:5]],
        },
        "verification_sandbox": (
            "not shipped: tantra.ai.verification.* (static AST checks, sandboxed execution, "
            "lookahead report) is documented design for a future wheel surface"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    print(json.dumps(run(), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
