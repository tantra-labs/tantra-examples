# Gap cascade: the `_kernel/` kernel-domain mirror (gaps 0001–0008)

**Status**: **all 8 gaps CLOSED**, 2026-11-15 — the `_kernel` mirror is fully dismantled; the remaining `_kernel/` files are only the shared harness.

## Summary

`tantra_examples/_kernel/` was a 166-file, kernel-verbatim Python mirror of the
source engine's domain layer. Every one of the eight wheel-surface gaps
(0001–0008) was "delete the mirror once the owning repo ships its wheel
surface" — and the surfaces form a **dependency cascade rooted in the kernel
domain**: the ai, adapters, data, and session mirrors import the domain
modules, so no gap could close before the root kernel-domain surface (gap
0006) landed in the `tantra` wheel. Parts of the mirror were float-based
(kernel `Bar`, `Position.quantity: float`, `Trade.quantity: float`,
`Instrument.lot_size: float`), which conflicts with the workspace zero-floats
policy — so the root was re-architected **Decimal-canonical** in the wheel, not
promoted verbatim.

**Root resolved (2026-11-15)**: the Decimal-canonical wheel kernel-domain layer
is complete; the mirror's kernel-domain portion (17 root modules + the
`indicators`/`portfolio_strategy`/`wire`/`backtest` subpackages + `native.py`)
was **deleted**; every `_kernel.*` consumer (kept mirror modules, the
`tantra_examples` SDK, examples, tests) was **retargeted to the wheel**; the
`[[tool.mypy.overrides]]` block was dropped. **Cascade complete 2026-11-15**:
every downstream gap mirror (`ai`, `data`, `screener`, `markets/india`, `cli`,
`adapters`, `session`) was then promoted into its wheel / `tantra_data`
surface and deleted in its own closure (ex 0002/0003/0004/0007/0008).

## Gap table

| # | Title | Owning repo(s) | Root `_kernel` dependency | Surface shippable now? | Closure path |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0001 | algo_analytics | tantra-runtime / tantra-ffi | `_kernel.base.Strategy` (typing), lazy `_kernel.session` | ✅ shipped in the wheel (2026-11-15) | `tantra.algo_analytics` + `tantra.quant` + `tantra.optimizer`; mirror deleted; imports retargeted |
| 0002 | ai-provider | tantra-agent / tantra-ffi | `_kernel.screener.catalog`, `_kernel.wire.screener`, `decision_guard` | ✅ **closed** 2026-11-15 | wheel `tantra.ai` (ask/decision/knowledge/llm.provider); `_kernel/ai/` + `fake_llm.py` + `decision_guard.py` deleted; 4 design-only scripts un-skipped |
| 0003 | data nav/loaders | tantra-data | `_kernel.bar` (float Bar), `_kernel.instrument`, `_kernel.data`, `_kernel.screener` | ✅ **closed** 2026-11-15 | `tantra_data.loaders.{amfi,nse,yfinance}` + `domain.quantity`; wheel `tantra.screener`; `_kernel/{data,screener}` + `amfi.py` + `bhavcopy.py` deleted; consumers retargeted |
| 0004 | display/universes/client | tantra-ffi / tantra-market | `universe_lists.py` → `_kernel.instrument`; `_kernel/markets/india/costs.py` → `_kernel.money` | ✅ **closed** 2026-11-15 | wheel `tantra.display` / `tantra.markets.india` / `tantra.markets.india.universes` / `tantra.cli.data`; mirrors deleted; `tantra.client` (REST) remains a separate future surface |
| 0005 | freeze-slicer | tantra-exec / tantra-ffi | none (pure Decimal) | ✅ shipped in the wheel (2026-11-15) | `tantra.sizing` freeze-slicing; `options/__init__.py` mirror removed; imports retargeted |
| 0006 | kernel-domain (the root) | tantra-ffi | the whole `_kernel/` tree | ✅ **closed** 2026-11-15 (all wheel slices shipped; kernel-domain mirror deleted; every `_kernel.*` import retargeted; mypy overrides dropped) | Decimal-canonical wheel domain layer; delete `_kernel/`; retarget every `_kernel.*` import; drop the `[[tool.mypy.overrides]]` block — done |
| 0007 | adapters-framework | tantra-adapters (framework) / tantra-ffi (`tantra.adapters`) | the `_kernel` domain web (`bar`, `instrument`, `order`, `order_state`, `position`, `tick`, `trade`, `money`, `execution`, `entities`, `wire`) | ✅ **closed** 2026-11-15 | wheel `tantra.adapters` framework namespace (registry/capabilities/contract/`FakeAdapter`/session/rate-limit/secrets); `_kernel/adapters/` deleted; `tantra-adapters` keeps shipping the broker ACL through the `tantra.adapters` entry-point group; `rest.py`/`gateway.py` stay excluded until `tantra.client` ships |
| 0008 | session | tantra-runtime / tantra-ffi | `_kernel` protocol types | ✅ **closed** 2026-11-15 | wheel `tantra.backtest.session` (`Tantra.backtest`: next-open fills, NSE delivery costs, T+1 settlement); `algo_analytics` retargeted + default runner; `_kernel/session.py` deleted |

## Execution order

1. ex 0005 + ex 0001 — the `_kernel`-independent surfaces (done 2026-11-15).
2. ex 0006 — the Decimal-canonical root: all wheel slices + the kernel-domain
   mirror deletion + full retarget (done 2026-11-15; see the gap table).
3. ex 0007 — `tantra.adapters` framework namespace (done).
4. ex 0003 — data loaders to `tantra_data` + wheel `tantra.screener` (done).
5. ex 0004 — display / universes / India market pack / CLI-data (done).
6. ex 0002 — `tantra.ai` on top of the screener slices (done).
7. ex 0008 — session orchestrator (done, last).

## Zero-floats note

The `_kernel` mirror contained float financial fields; the wheel surface is
Decimal-canonical (never promoted verbatim). The root closure therefore
included a Decimal re-architecture, which is why the root (ex 0006) was a
re-architecture rather than a move. The shared harness that remains in
`_kernel/` is Decimal-canonical against the wheel; the float-rooted pre-existing
test failures in the kept harness (e.g. `tantra_examples/metrics.fills_equity_curve`)
are tracked by the owning gaps.
