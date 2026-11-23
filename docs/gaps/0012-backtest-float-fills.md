# 0012 — `backtest.py` carries float quantity/price in public records and two engines in one module

**Status**: open
**Filed**: 2026-11-23 — workspace design review (root plan 0021) · **Kind**: design-flaw · **Severity**: medium
**Plan**: [0006](../plans/0006-design-review-2026-11.md)

## What's stubbed or hardcoded

- `tantra_examples/backtest.py:233-234,248`: `FillRecord.quantity: float`, `FillRecord.price: float` and `OrderEvent.quantity: float`, while `tantra_examples/backtest.py:69` advertises a "Zero-friction, zero-float backtester".
- `tantra_examples/backtest.py:213-225`: the engine is a "verbatim graft" sitting next to a separate fresh implementation, so two backtest paths live in one 502-line module.
- A third path exists in the wheel: `tantra-ffi/python/tantra/backtest/session.py` (`tantra.backtest.session`).

## Why

Float fills feed P&L tables that learners imitate, contradicting the zero-floats policy (`.agents/rules/interface-first-and-modularity.md` section 2.3). Two engines in one file invite divergent results for the same strategy, and a third in the wheel makes "which one is canonical" unanswerable for readers of the examples.

## How to close it

1. Change `FillRecord.quantity`, `FillRecord.price` and `OrderEvent.quantity` to `Decimal` (or the wheel's `Quantity`/`Price` types); remove float conversions in the engine.
2. Regenerate the snapshot goldens in `tests/snapshots/` and review the numeric diffs.
3. Write a parity test between the grafted engine, the fresh implementation and `tantra.backtest.session` on a synthetic lakehouse run; then fold the grafted engine into `tantra.backtest` or delete it.
4. Rewrite the module docstring and the "verbatim graft" comment to reference the real `tantra-*` paths.

**Verification**: `pytest -q tests/unit` with updated goldens; parity test green before deletion; `ruff check .`, `mypy tantra_examples`; grep-style test asserting no `float` annotations on fill/order records.

## Related

- Root gap 0021 (simulation/fill-model unification for research harnesses, beyond root plan 0019 P2.1).
- [0010](0010-metrics-float-and-wheel-duplication.md) — related float leakage in `metrics.py`.
- Adjacent to root plan 0006 follow-on `fills_equity_curve`; plan 0006 R3 (honba provenance comments in `backtest.py:213`).
