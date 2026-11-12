# 0008 — runtime-session-surface

**Status**: open
**Owning repo**: `tantra-runtime` (Strategy Tester session orchestrator) /
`tantra-ffi` (wheel surface).

## Symptom
The `tantra` wheel does not ship a session orchestrator that can run a strategy
against real (lakehouse) data with next-open fills, NSE delivery costs and T+1
settlement from outside `tantra-runtime` itself. The Stage 3 optimizer engine
mirrors (`tantra_examples/optimizer/algo_analytics/{walk_forward,monte_carlo,
plateau}.py`) need exactly that surface for their real-data code path: each calls
`Tantra.backtest(...)` for a fold/trial/grid-point run.

## What stands in (mirror)
`tantra_examples/_kernel/session.py` — a custom (non-verbatim) trim pinning only
the static protocol shape the engine mirrors read against:
* `DataProvider` (Protocol): `bars(instrument_id, *, timeframe, start, end)`,
  `instrument(instrument_id)`.
* `CostModel` (Protocol): `apply(trade) -> Trade`.
* `BacktestResult` (Protocol): `strategy_name`, `metrics`, `equity_curve`.
* `Tantra`: a session-factory stub. `Tantra.backtest(...)` raises
  `NotImplementedError` unconditionally — loud failure by design, matching
  the wheel-missing state, rather than a silent synthetic fallback.

This keeps the walk-forward/Monte-Carlo/plateau engines fully type-checkable and
runnable end-to-end on synthetic data (via `_kernel.testing.replay`, not
`Tantra.backtest`); only the real-data orchestration path is blocked, and it
fails with a clear message naming this gap.

## Consumers
`tantra_examples/optimizer/algo_analytics/walk_forward.py` (`_run_factory`'s
`run` closure), `monte_carlo.py`, `plateau.py` — each lazily imports
`_kernel.session.Tantra` only inside the real-data branch, so synthetic-data
callers never touch this stub.

## How to close
Ship the Strategy Tester session surface through `tantra-ffi` (a `tantra`
wheel class equivalent to `Tantra.backtest(strategy, start, end, ...)` that
runs next-open fills with NSE delivery costs and T+1 settlement against the
lakehouse). Then delete `_kernel/session.py`, retarget the three
`algo_analytics` consumers' `from tantra_examples._kernel.session import
Tantra` to the wheel surface, and drop the `NotImplementedError` branch.
