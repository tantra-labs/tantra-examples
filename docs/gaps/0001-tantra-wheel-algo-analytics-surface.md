# 0001 — tantra-wheel-algo-analytics-surface

**Status**: open
**Owning repo**: `tantra-runtime` (enhancer crates: GA / Bayesian / WFO / DSR) and
`tantra-ffi` (the `tantra` wheel surface that must expose them).

## Symptom
The `tantra` wheel does not expose the analytics engine the honba harness relied on
(`honba.algo_analytics.{walk_forward, folds, monte_carlo, deflated_sharpe, plateau}`), so
the ported examples cannot call the engine for walk-forward optimisation, fold generation,
Monte-Carlo permutation runs, plateau analysis, or Deflated Sharpe grading.

## What stands in (mirror)
* `tantra_examples/optimizer/algo_analytics/` — pure-Python mirrors of the engine
  algorithms: `walk_forward.py`, `folds.py`, `monte_carlo.py`, `plateau.py`,
  `deflated_sharpe.py`, `metrics.py`.
* `tantra_examples/optimizer/__init__.py` — Pareto-frontier helpers
  (`extract_pareto_frontier`, `plot_pareto`, `sharpe_sortino_dd`).
* `tantra_examples/quant.py` — exact-`Decimal` statistical helpers (DSR, PBO, covariance,
  OLS, Black-Scholes Greeks) mirroring the Rust engine math for the flat 12–15 examples.

Each mirrored file carries a `# mirror: engine-verbatim port (gap 0001)` citation after
its docstring.

Consumers (the example scripts, not the harness):
`examples/backtesting/04_walk_forward.py`, `05_monte_carlo.py`, `examples/optimizer/01`,
`02`, `03`, `examples/ai_research/10_claude_autonomous_quant.py`,
`12_ai_drawdown_refinement.py`, and flat `examples/12`–`15` via `quant.py`.

## How to close
Ship the same surface from `tantra-runtime` through `tantra-ffi` (wheel `algo_analytics`
namespace or equivalent), then delete the mirrors and retarget the imports. Until then the
staged port keeps byte-comparable semantics so the golden parity tests pin the mirror
behaviour.
