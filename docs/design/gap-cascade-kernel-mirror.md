# Gap cascade: the `_kernel/` kernel-domain mirror (gaps 0001–0008)

**Status**: verified dependency analysis, 2026-11-15.

## Summary

`tantra_examples/_kernel/` is a 166-file, kernel-verbatim Python mirror of the
source engine's domain layer. Every one of the eight wheel-surface gaps
(0001–0008) is "delete the mirror once the owning repo ships its wheel
surface" — and the surfaces form a **dependency cascade rooted in `_kernel/`**:
the ai, adapters, data, and session mirrors import `_kernel.*` domain modules,
so no single gap can close before the root kernel-domain surface (gap 0006)
lands in the `tantra` wheel. Parts of `_kernel` are float-based (kernel `Bar`,
`Position.quantity: float`, `Trade.quantity: float`, `Instrument.lot_size:
float`), which conflicts with the workspace zero-floats policy for a wheel
surface — so the root is being re-architected **Decimal-canonical**, not
promoted verbatim.

## Gap table

| # | Title | Owning repo(s) | Root `_kernel` dependency | Surface shippable now? | Closure path |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0001 | algo_analytics | tantra-runtime / tantra-ffi | `_kernel.base.Strategy` (typing), lazy `_kernel.session` | ✅ shipped in the wheel (2026-11-15) | `tantra.algo_analytics` + `tantra.quant` + `tantra.optimizer`; mirror deleted; imports retargeted |
| 0002 | ai-provider | tantra-agent / tantra-ffi | `_kernel.screener.catalog`, `_kernel.wire.screener`, `decision_guard` | blocked | `tantra.ai` wheel namespace after the screener/wire Decimal slices; delete `_kernel/ai/` + `fake_llm.py` shim; un-skip design-only scripts |
| 0003 | data nav/loaders | tantra-data | `_kernel.bar` (float Bar), `_kernel.instrument`, `_kernel.data`, `_kernel.screener` | blocked | re-point `amfi.py`/`bhavcopy.py`/`_kernel/{data,screener}` to `tantra_data` once the Decimal `bar`/`instrument` surface lands (API rewrite, not a straight re-point) |
| 0004 | display/universes/client | tantra-ffi / tantra-market | `universe_lists.py` → `_kernel.instrument`; `_kernel/markets/india/costs.py` → `_kernel.money` | partial | wheel `tantra.display` / `tantra.markets.india` / `tantra.universes` after the domain-core slice; `tantra.client` (REST) is a separate future surface |
| 0005 | freeze-slicer | tantra-exec / tantra-ffi | none (pure Decimal) | ✅ shipped in the wheel (2026-11-15) | `tantra.sizing` freeze-slicing; `options/__init__.py` mirror removed; imports retargeted |
| 0006 | kernel-domain (the root) | tantra-ffi | the whole `_kernel/` tree | in progress (domain-core + bar/tick/order/order_state + execution + indicators + base layer + declarative/portfolio_strategy + wire shipped) | Decimal-canonical wheel domain layer; delete `_kernel/`; retarget every `_kernel.*` import; drop the `[[tool.mypy.overrides]]` block |
| 0007 | adapters-framework | tantra-adapters (framework) / tantra-ffi (`tantra.adapters`) | the `_kernel` domain web (`bar`, `instrument`, `order`, `order_state`, `position`, `tick`, `trade`, `money`, `execution`, `entities`, `wire`) | blocked | `tantra.adapters` framework namespace + the domain core; `tantra-adapters` ships the broker ACL (different API), so no straight re-point; drop the `rest.py`/`gateway.py` exclusion once `tantra.client` ships |
| 0008 | session | tantra-runtime / tantra-ffi | `_kernel` protocol types | blocked | runtime Strategy Tester session orchestrator over the lakehouse (next-open fills, NSE costs, T+1); delete `_kernel/session.py`; retarget the three `algo_analytics` consumers |

## Execution order

1. ex 0005 + ex 0001 — the `_kernel`-independent surfaces (done 2026-11-15).
2. ex 0006 — Decimal-canonical domain-core slices, bottom-up: `money` /
   `position` / `trade` / `instrument` / `entities` (shipped in the wheel
   2026-11-15), then the float kernel `bar` Decimal-canonical (shipped
   2026-11-15: `tantra.bar.Bar`), then `tick` + `order` + `order_state`
   (shipped 2026-11-15: `tantra.tick`, `tantra.order`, `tantra.order_state`
   FSM), then `execution` (shipped 2026-11-15: `tantra.execution`), then
   `indicators` (87 files — shipped 2026-11-15: all 8 families, 74 registered
   kinds, `tantra.indicators` registry package), then the kernel strategy base
   layer (`tantra.base`/`tantra.context`/`whole_shares`, shipped 2026-11-15),
   then `declarative` + `portfolio_strategy` (shipped 2026-11-15), then `wire`
   (`tantra.wire`, pydantic, shipped 2026-11-15), then `store` / `backtest` sims.
3. ex 0004 — display / universes / India market pack on top of the domain core.
4. ex 0003 — re-point data loaders to `tantra_data`.
5. ex 0002 — `tantra.ai` on top of the screener/wire slices.
6. ex 0007 — `tantra.adapters` framework namespace.
7. ex 0008 — session orchestrator (last; needs the runtime).

## Zero-floats note

The `_kernel` mirror contains float financial fields; the wheel surface is
Decimal-canonical (never promoted verbatim). Each closure therefore includes a
Decimal re-implementation step, which is why the root (ex 0006) is a
re-architecture rather than a move.
