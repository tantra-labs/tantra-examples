# 0001 — tantra-wheel-algo-analytics-surface

**Status**: open
**Owning repo**: `tantra-runtime` (enhancer crates: GA / Bayesian / WFO / DSR) and
`tantra-ffi` (the `tantra` wheel surface that must expose them).

## Symptom
The `tantra` wheel does not expose the analytics engine the honba harness relied on
(`honba.algo_analytics.{walk_forward, folds, monte_carlo, deflated_sharpe}`), so the
ported examples cannot call the engine for walk-forward optimisation, fold generation,
Monte-Carlo permutation runs, or Deflated Sharpe grading.

## What stands in (mirror)
* `tantra_examples/optimizer/` — pure-Python mirrors of the engine algorithms.
* `tantra_examples/quant.py` — statistical helpers (DSR etc.) mirroring the engine math.

Consumers ported in Stage 1 (`pipeline/` manifest/reporting, `sip_*`) and the Stage 3
tester/enhancer examples import these mirrors through the D5 retargets.

## How to close
Ship the same surface from `tantra-runtime` through `tantra-ffi` (wheel `algo_analytics`
namespace or equivalent), then delete the mirrors and retarget the imports. Until then the
staged port keeps byte-comparable semantics so the golden parity tests (Stage 3) pin the
mirror behaviour.
