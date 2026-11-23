# 0010 — `metrics.py` claims exact Decimal but ships float metrics duplicating the wheel

**Status**: open
**Filed**: 2026-11-23 — workspace design review (root plan 0021) · **Kind**: duplication · **Severity**: medium
**Plan**: [0006](../plans/0006-design-review-2026-11.md)

## What's stubbed or hardcoded

- `tantra_examples/metrics.py:1-5` docstring promises "exact Decimal ... free of binary floating point", while `tantra_examples/metrics.py:310-376` (`exposure_metrics`, `max_drawdown`, `sharpe_ratio`, `sortino_ratio`) use `float` and `math.sqrt` over `curve[...]["value"]`.
- `sharpe_ratio(curve, capital)` and `sortino_ratio(curve, capital)` take an unused `capital: float` (`tantra_examples/metrics.py:335`, `:354`) and share a copy-pasted returns block (`:340-346` vs `:359-365`).
- `SESSIONS_PER_YEAR = 252` is redefined at `tantra_examples/metrics.py:139`.
- Wheel equivalents already exist: `tantra-ffi/python/tantra/algo_analytics/metrics.py:20` (`sharpe_ratio`) and `tantra-ffi/python/tantra/optimizer.py:78` (`sharpe_sortino_dd`).
- Teaching code does float P&L: `examples/optimizer/01_ga_trend_breakout.py:126,134,163` and `examples/optimizer/02_bayesian_mean_reversion.py:86,107,114` use `float(fill.price)` / `float(f.price - entry_price) * float(f.quantity)`.

## Why

The zero-floats policy (`.agents/rules/interface-first-and-modularity.md` section 2.3) is violated in the repo learners copy from. Two Sharpe definitions (sample std here, the wheel's own) can disagree on the same equity curve, and the docstring claims a guarantee the code does not provide.

## How to close it

1. Delete the float helpers in `tantra_examples/metrics.py` and call the wheel functions (`tantra.algo_analytics.metrics`, `tantra.optimizer`); if the wheel lacks a Decimal-curve adapter, file it in tantra-ffi and add it there.
2. Remove the unused `capital` parameters and the duplicated returns block; keep one `SESSIONS_PER_YEAR` source (the wheel's).
3. Rewrite the two optimizer examples to accumulate `Decimal` P&L and convert to float only at display time.
4. Fix the module docstring to match what remains.

**Verification**: a `hypothesis` test in `tests/unit/` comparing the retargeted metrics with the wheel's on random Decimal curves; `ruff check .`, `mypy tantra_examples`, `pytest -q tests/unit`; update any snapshot goldens that change.

## Related

- Root gap 0015 (pricing and quant math single source); provider repo tantra-ffi (wheel `tantra.algo_analytics`).
- [0012](0012-backtest-float-fills.md) — same float leakage in `backtest.py`.
- Adjacent to root plan 0006 follow-on "`fills_equity_curve` Decimal end-to-end" (different functions).
