# Gap Cascade — the `_kernel/` Kernel-Domain Mirror as the Shared Root of Gaps 0001–0008

`tantra_examples/_kernel/` is a **166-file kernel-domain mirror** standing in for wheel
surfaces that the owning repos have not shipped yet. Every one of gaps 0001–0008 is a
variant of the same instruction: *delete the mirror once the owning repo ships its wheel
surface*. None of the gaps can close in isolation, because the mirrored surfaces form a
dependency cascade rooted in the `_kernel` domain itself: the domain types (`bar`,
`instrument`, `order`, `position`, `trade`, `money`, `execution`, `order_state`,
`entities`, `wire`) are imported by the higher-level mirror surfaces (`adapters`, `ai`,
`markets.india`, `data`, `screener`), so the root domain surface (gap 0006) must ship
first (as a Decimal-canonical wheel slice), and each dependent gap closes only once its
own surface lands on top of that. This note records the verified dependency reality of
all eight gaps (probe-verified 2026-11-14) and the execution order for closing them.

## Dependency map (probe-verified 2026-11-14)

| # | Gap (title) | Owning repo(s) | Root `_kernel` dependency | Surface shippable now? | Closure path |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0001 | tantra-wheel-algo-analytics-surface | `tantra-runtime` / `tantra-ffi` | `_kernel.base.Strategy` + lazy `_kernel.session` | **yes — shipping in the wheel (parallel batch)** | wheel `tantra.algo_analytics` + delete mirror (`optimizer/algo_analytics/`, `quant.py`) + retarget consumers |
| 0002 | tantra-wheel-ai-provider-surface | `tantra-agent` / `tantra-ffi` | `_kernel.screener.catalog`, `_kernel.wire.screener`, `decision_guard` | no — blocked on the ex 0006 `screener`/`wire` sub-slices + a `tantra.ai` wheel namespace | wheel `tantra.ai` + delete `_kernel/ai/` + `fake_llm.py` provider shim + un-skip design-only scripts |
| 0003 | tantra-data-nav-loaders | `tantra-data` | `_kernel.bar` (float Bar), `_kernel.instrument`, `_kernel.data`, `_kernel.screener` | no — `tantra_data` ships the lakehouse but not the same loader API (API-rewrite, not a straight re-point); blocked on the ex 0006 Decimal bar/instrument surface | re-point `amfi.py`/`bhavcopy.py`/`_kernel/{data,screener}` to `tantra_data` after the Decimal-canonical bar surface lands + drop the env seam where the real surface covers CI |
| 0004 | tantra-wheel-display-universes-client | `tantra-ffi` (`tantra.display`, `tantra.client`, `tantra.markets.india`) / `tantra-market` | `universe_lists.py` → `_kernel.instrument`; `_kernel/markets/india/costs.py` → `_kernel.money` (`display_style.py`/`output.py`: none — independent) | partial — `display_style`/`output` are independent; universes/india blocked on the ex 0006 domain-core slice; `tantra.client` (REST) does not exist yet | ship wheel `display`/`markets.india`/`universes` after the domain-core Decimal slice, delete mirrors, retarget; `tantra.client` is a separate future surface |
| 0005 | tantra-exec-freeze-slicer-mirror | `tantra-exec` / `tantra-ffi` | none — independent (pure Decimal) | **yes — shipping in the wheel `tantra.sizing` (parallel batch)** | wheel `Sizer.slice_order`/`verify_slices`/`freeze_limit_qty` + delete the `options/__init__.py` mirror + retarget `examples/options/07` and `examples/stocksharp/02` |
| 0006 | tantra-wheel-kernel-domain-surface (the root) | `tantra-ffi` | the whole `_kernel/` tree (the root itself) | partial — Decimal `money`/`position`/`trade`/`instrument`/`entities` wheel slice **started in the parallel batch**; the remainder (float kernel `bar`, `indicators` 87 files, `execution`, `order_state`, `portfolio_strategy`, `session`, `wire`, `backtest` sims, `store`) needs the Decimal-canonical re-architecture | full wheel domain layer + delete `_kernel/` + retarget every `_kernel.*` import + drop the `[[tool.mypy.overrides]]` block |
| 0007 | tantra-adapters-framework-surface | `tantra-adapters` (framework) / `tantra-ffi` (`tantra.adapters`) | the `_kernel` domain web: `bar`/`instrument`/`order`/`order_state`/`position`/`tick`/`trade`/`money`/`execution`/`entities`/`wire` | no — not closeable by re-pointing to `tantra-adapters` (that repo ships the broker ACL — `dhan.py`/`zerodha.py`/`common/models.py`/`PaperBroker`/registry — a different API); needs a framework namespace + the domain core | ship the framework namespace (same public names: `Adapter`, `ExecutionAdapter`, `MarketDataAdapter`, `resolve_adapter`, `available_adapters`, `FakeAdapter`, error/capability types) + delete `_kernel/adapters/` + drop the `rest.py`/`gateway.py` exclusion once `tantra.client` (ex 0004) ships |
| 0008 | runtime-session-surface | `tantra-runtime` / `tantra-ffi` | `_kernel` protocol types (`_kernel/session.py` Protocols, domain types) | no — needs the runtime Strategy Tester session orchestrator over the lakehouse (next-open fills, NSE costs, T+1); not shippable from `tantra-examples` | wheel session surface + delete `_kernel/session.py` + retarget the three `algo_analytics` consumers (`walk_forward.py`, `monte_carlo.py`, `plateau.py`) |

## Execution order

1. **Ship the two independent surfaces first (parallel batch):** ex 0005 (`tantra.sizing`
   freeze slicer, pure Decimal) and ex 0001 (`tantra.algo_analytics`) — neither waits on
   the domain cascade.
2. **Ex 0006 domain-core slices, bottom-up:** `money` → `position` → `trade` →
   `instrument` → `entities` first (Decimal-canonical), then the float kernel `bar`
   re-architected Decimal-canonical, then the rest (`indicators`, `execution`,
   `order_state`, `portfolio_strategy`, `session`, `wire`, `backtest` sims, `store`).
3. **Ex 0004** display/universes/india — depends on the domain-core slice (`_kernel.money`,
   `_kernel.instrument`); `display_style`/`output` could ship earlier but are kept with
   the surface batch.
4. **Ex 0003** data re-point — depends on the Decimal-canonical `bar`/`instrument`
   surface; an API-rewrite against `tantra_data`'s real loader API, not a re-point.
5. **Ex 0002** ai — depends on the ex 0006 `screener`/`wire` sub-slices shipping first.
6. **Ex 0007** adapters framework — depends on the domain core + a framework namespace;
   `tantra-adapters` (broker ACL) is deliberately *not* the closure target.
7. **Ex 0008** session — last; needs the runtime Strategy Tester session orchestrator.

## Zero-floats note

The `_kernel` mirror contains float financial fields (kernel `Bar`,
`Position.quantity: float`, `Trade.quantity: float`, `Instrument.lot_size: float`) that
conflict with the workspace zero-floats policy for a shipped wheel surface. The wheel
surface must therefore be **Decimal-canonical** — never promoted verbatim from the mirror
— so every closure above includes a Decimal re-implementation step before the mirror is
deleted and consumers are retargeted. This is the reason ex 0006 is re-architected
Decimal-canonical rather than shipped by verbatim promotion.
