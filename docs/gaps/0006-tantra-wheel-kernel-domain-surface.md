# 0006 — tantra-wheel-kernel-domain-surface

**Status**: open
**Owning repo**: `tantra-ffi` (compiled `tantra` wheel; the kernel-domain engine surface
behind it), sourced from the tamashii-class Rust engine of the ecosystem.

## Symptom
The `tantra` wheel exposes no kernel-domain engine surface yet — no `InstrumentId`,
`Bar`, `OrderIntent`, Strategy base, numerics evaluator, parquet store, coverage /
service plumbing, strategy manifest/wire contracts, or the compiled-extension attributes
(`SCHEMA_VERSION`, `API_VERSION`, `STRATEGY_API_VERSION`, `currency_minor_units`) that
kernel-verbatim harness code reads through `honba._native` in the owning engine.

## What stands in (mirror)
`tantra_examples/_kernel/` — the kernel mirror, **166 files**:

**Root modules (33)**: `bar`, `base` (Strategy, Parameter), `calendar`, `config`
(StrategyConfig), `context`, `coverage`, `declarative` (DeclarativeStrategy,
TargetWeightStrategy, Entry), `entities` (domain + wire re-exports), `evaluator`,
`execution` (intent→event execution FSM with the legacy `ExecutionPort` event
projection), `greeks` (Black-Scholes + option Greeks), `instrument`, `loader`
(find_catalog / load_catalog_strategy / CatalogError), `log`, `manifest` (StrategyManifest,
ParameterSpec…), `money`, `native` (extension-attribute stand-in), `option`, `order`,
`order_state`, `portfolio`, `ports`, `position`, `risk`, `runner` (StrategyRunner +
risk/warm-up gates), `service`, `session` (see gap 0008), `sizing` (`whole_shares`),
`store` (ParquetBarStore + `find_data_root`), `testing` (replay), `tick`, `trade`.

**Subpackages**:
* `adapters/` (13 files) — gap 0007.
* `ai/` (6 files) — gap 0002.
* `backtest/` (5 files) — `simulated`, `impact`, `l2_sim`, `opening_auction`.
* `cli/` (1 file) — gap 0004.
* `data/` (1 file) — gap 0003.
* `indicators/` (**87 files**) — `_base` (`Indicator`, `@indicator` registry), `_util`,
  `_rolling`, `_india`, `bank` (`IndicatorBank`), and the family packages
  `moving_average` (incl. `averages.make_ma`), `trend`, `momentum`, `volatility`,
  `volume`, `support_resistance`, `breadth`, `statistical`.
* `markets/india/` (3 files) — gap 0004.
* `portfolio_strategy/` (**10 files**) — tamashii `strategies/portfolio` renamed so it does
  not collide with the already-mirrored `_kernel/portfolio.py` domain module
  (`strategy`, `factory`, `universe`, `weighting`, `schedule`, `selection`, `scoring`,
  `stats`, `view`, …).
* `screener/` (2 files) — gap 0002/0003.
* `wire/` (4 files) — `base`, `wire`, `screener`, `__init__` (envelope + `SCHEMA_VERSION`
  check).

`_kernel/entities.py` binds **both** domain and wire re-exports (wire last, mirroring
tamashii `entities/__init__`), so code needing the FSM `OrderEvent` imports
`_kernel.order_state` directly (e.g. `_kernel/execution.py`) — not `entities`.

mypy: `[[tool.mypy.overrides]]` in `pyproject.toml` disables the `override` error
code for `_kernel.indicators.*`, `_kernel.declarative`,
`_kernel.portfolio_strategy.*` — the registry's typed `update` specializations
conflict with the base `Indicator` protocol by design.

Each mirrored file carries a `# mirror: kernel-verbatim port (gap 0006|0007)` citation
line after its docstring, a per-file `# ruff: noqa: …` accommodation header
(`E501` where kernel formatting is byte-verbatim, `UP036` for the tomllib guard,
`B027` for the intentionally-empty lifecycle hooks) and
inline `# mirror accommodation (gap 0006)` `type: ignore[...]` comments where the
verbatim kernel assigns dynamic class attributes or typed-unions; runtime costs stay
exactly as the kernel had them.

## Pinned constants (delete when the surface exists)
* `native.py`: `SCHEMA_VERSION = 8`, `API_VERSION = "v1"`, `STRATEGY_API_VERSION = "1.0.0"`,
  currency-minor-units table — sourced from the owning engine's Rust constants
  (`lib.rs`, `manifest.rs`).

## Consumers beyond `_kernel/`
`amfi.py` (DateInterval via `_kernel.coverage`), `backtest.py`, `bars.py`,
`decision_guard.py`, `ewr/simulation.py`, `replay_report.py`, `catalog.py`, `sip.py`,
`sip_plan.py`, `screening/nl_support.py`, `synthetic.py` (kernel Bar fixtures — the
harness world uses float kernel bars while the fresh-example Decimal world is
`data.py`), `universe_lists.py` (`find_data_root`), `settlement.py`, and the `options/*`
best-effort `tantra.client.get_instrument` try-import (directionally also gap 0004).

## How to close
Ship the domain layer through `tantra-ffi` (kernel types, strategy contract manifests,
wire schemas, parquet store, evaluator, compiled attributes via the wheel's native
module) **plus** the Stage-2 extension surface: the indicator registry/families,
`declarative`/`execution`/`sizing`, and `portfolio_strategy` (as a matching subpackage
name on the wheel). Then delete `_kernel/` together with `native.py`, retarget every
`_kernel.*` import to the wheel surface, and drop the `[[tool.mypy.overrides]]`
override block; the mirror accommodations evaporate with it.
