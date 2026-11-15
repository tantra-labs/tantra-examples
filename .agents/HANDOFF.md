# `tantra-examples` — Inter-Agent Handoff

## Latest Batch
* **Gaps 0001 + 0005 CLOSED (2026-11-15, T9.3 + T9.7)** — the owning wheel surfaces shipped
  in `tantra-ffi` (`d79d31b` + `6ac14dd`): `tantra.algo_analytics` + `tantra.quant` +
  `tantra.optimizer` (ex 0001) and `tantra.sizing` freeze-slicing `freeze_limit_qty` /
  `slice_order` / `verify_slices` (ex 0005). This repo then **deleted the mirrors**
  (`tantra_examples/optimizer/` package + `quant.py`; the freeze-slicing block in
  `tantra_examples/options/__init__.py`) and **retargeted every consumer** to the wheel:
  `examples/backtesting/04/05`, `ai_research/10/12`, `optimizer/01/02/03`,
  `options/06/07`, `stocksharp/02`, flat `12/14/15`, `tests/unit/test_02_twap_vwap` +
  `test_07_large_qty_options_slicer`, and the `docs/reference/*.md` module paths.
* **ex 0006 (the kernel-domain root) STARTED** — Decimal-canonical domain-core slice shipped
  in the wheel (`tantra.money` / `position` / `trade` / `instrument` / `entities`); **Wave 1**
  retargeted the financial leaf modules to the wheel — `markets/india/costs` (Decimal rates +
  wheel `Money` fill costs), `portfolio` (`Account`/`Portfolio` on Decimal-major `Money`),
  `risk.check_state` (Decimal), `evaluator` (wheel `Bar` series math); **Wave 2** retargeted the
  config-ish leaf modules — `config` (wheel `InstrumentId`), `option` (Decimal contract),
  `greeks` (Decimal Black-Scholes + portable A&S 7.1.26 normal CDF), `ports` (wheel `Bar`/
  `CoverageRecord`/`DateInterval`/wire screener), `manifest` (wheel `InstrumentId` + wire types,
  pinned `STRATEGY_API_VERSION="1.0.0"`), `loader` (wheel `Strategy`), `screener/coverage`
  (`tantra.coverage.DateInterval`), `cli` (`tantra.store.ParquetBarStore`), `data`
  (Decimal quantity parser); `calendar`/`log`/`screener/catalog` were Decimal-free and unchanged.
  **Wave 3** retargeted `runner`/`testing` (wheel `tantra.backtest.bar_close_fills.BarCloseFills`
  + Decimal `Bar`/`OrderIntent`/`Trade`), `session`, `service`. **Wave 4** retargeted the
  `adapters` subpackage (gap 0007 dependency-unblock) and the `ai` subpackage (gap 0002
  dependency-unblock): `adapters/*` now drives wheel `tantra.{bar,instrument,order,order_state,
  position,tick,trade,money,execution,wire.wire}` Decimal types end to end (models are
  Decimal-coercing; `FakeAdapter` passes the full `verify_adapter_contract`; `secrets` lazy-imports
  the optional `cryptography`), and `ai/ask` builds `tantra.wire.screener` DTOs (`ai/decision`
  stays a `decision_guard` re-export — no wheel `tantra.ai` decision surface yet, per gap 0002).
  **Wave 5a** retargeted the simple outer consumers of the shipped `_kernel` leaf modules to the
  wheel: `universe_lists` (wheel `InstrumentId` + `tantra.store.find_data_root`), `bars`
  (`tantra.bar.Bar`), `synthetic` (wheel Decimal `Bar` builders), `amfi` (Decimal NAV bars +
  wheel `Bar`/`InstrumentId`/`coverage`), `bhavcopy` (Decimal OHLCV wheel `Bar`),
  `ewr/simulation` (wheel `Bar`), `sip_plan` (wheel `coverage`/`instrument`/`store`),
  `base` (wheel `Bar`/`InstrumentId`/`DateInterval`/`ParquetBarStore`), `decision_guard`
  (wheel `OrderIntent`/`OrderSide`/`OrderType`, float→Decimal boundary at `float(intent.quantity)`).
  `catalog` + `screening/nl_support` untouched (only kept modules `_kernel.loader`/`evaluator`).
  **Wave 5b (final, ex 0006 closure)**: deleted the shipped `_kernel` mirror — 17 root modules
  (`bar`/`base`/`context`/`coverage`/`declarative`/`entities`/`execution`/`instrument`/`money`/
  `order`/`order_state`/`position`/`sizing`/`store`/`tick`/`trade`/`native`) + the `indicators`/
  `portfolio_strategy`/`wire`/`backtest` subpackages — rewrote `_kernel/__init__.py` as a wheel
  facade (`tantra.{bar,instrument,money,order,position,tick,trade}` + kept `_kernel.portfolio`),
  fixed the last `_kernel.*` straggler imports (`evaluator`→`tantra.wire.screener`,
  `risk`/`runner`→local `_native_attr` reading wheel `SCHEMA_VERSION`/`API_VERSION`,
  `testing`→`tantra.wire`, `adapters.testing`→`tantra.store`+`tantra.coverage`), and dropped the
  `[[tool.mypy.overrides]]` block. Verified: `_kernel` import + facade checks pass, ruff clean on
  touched files, unit run = 838 passed / 72 failed (pre-existing float-rooted, e.g.
  `metrics.fills_equity_curve`) / 3 errors (`test_07_run_via_client`, `httpx` optional dep absent)
  / 50 skipped. Status: shipped-mirror deletion complete; the remaining `_kernel` files are
  other-gap mirrors (0002/0003/0004/0007/0008) — ex 0006 stays open for the compiled risk/
  trading-state surface.
* **Blocker analysis + dependency map**: verified the 8-gap cascade rooted in the 166-file
  `_kernel` mirror (`docs/design/gap-cascade-kernel-mirror.md`); gap docs 0002/0003/0004/
  0007/0008 carry `open — blocked` status with precise blockers; 0006 `in progress`.
* **Gates**: full `pytest` green except one pre-existing environmental failure
  (`test_mutual_fund_screener_execution` needs the 1D NSE catalog on disk); `ruff check` +
  `ruff format --check` clean (incl. pre-existing I001/SIM102 in untouched files fixed).

## Phase / Slice Status
* **Honba staged port (plan 0002)** — **ALL 9 STAGES COMPLETE (Stages 0–8)**; recorded Implemented in `docs/plans/README.md` (commit `bbfa692`). Plan doc cleaned up per gap-tracking §4.
* **Docs (this change)**: former `docs/roadmap/` (`roadmap.md` + `migration-verification.md`) dismantled into `docs/design/` (`architecture.md`, `implementation-record.md`, `code-migration-map.md`), `docs/gaps/` (README + 0001–0008 source-verified), and `docs/plans/README.md`; `docs/reference/` concept docs unchanged.
* Full verification gates were green at port close: `pytest -q` (922 passed, 70 skipped), `ruff check .`, `ruff format --check .`, `mypy tantra_examples` (234 files), `make check`.

## Decisions & Discoveries
* **Pytest import mode & test structure**: `pythonpath = ["."]` in `pyproject.toml` + empty `__init__.py` in `tests/`, `tests/unit/`, `tests/integration/` lets `pytest -q` run from the repo root and resolves module-name collisions between unit and integration tests.
* **Kernel mirror is the wheel-missing stand-in**: `tantra_examples/_kernel/` was a 166-file kernel-verbatim mirror (indicators 87, portfolio_strategy 10, adapters 13) cited against gaps 0002–0008. The ex 0006 closure (Wave 5b) deleted the shipped modules and the `[[tool.mypy.overrides]]` block; `SCHEMA_VERSION`/`API_VERSION` now come from the wheel (`tantra.SCHEMA_VERSION`/`tantra.API_VERSION`). The remaining `_kernel` files (adapters/ai/calendar/cli/config/data/greeks/loader/log/manifest/markets/option/ports/screener/service/session + kept evaluator/risk/runner/testing/portfolio) still mirror the not-yet-shipped surfaces.
* **Gap 0004 stream plumbing**: the standalone screener CLIs stream through `screener_cli.py` + `pipeline/io.py` (`read_symbols`/`to_stream`/`parse_symbols`/`dumps`), not a `stream.py` module.
* **Gap 0005**: only `examples/options/07_large_qty_options_slicer.py` probes optional `tantra_te_slicer`; `examples/stocksharp/02_twap_vwap.py` imports `tantra_examples.options` directly.
* **Pitfalls contract**: flat foundational scripts (15) have 2–3 bullets; topic scripts (94) have 3–6. `test_pitfalls_sections.py` accommodates both.
* **Offline catalog seam**: integration tests that require the multi-GB real Parquet catalog skip when run offline (`VYAAPAAR_DATA_DIR` synthetic fixture seam, gap 0003).

## Immediate Next Step
* All 9 stages of the `honba-examples` port are complete and verified; docs batch committed.
* Next open work is gap-driven (all 0001–0008 owned by other repos): close a gap when its owning surface ships, then delete the mirror/stub and retarget consumers.

## Operating Invariants
* Zero floats in financial math (documented exceptions: BS internals example 13; grafted `metrics.py` stats; kernel-mirror float domain, gap 0006). Deterministic offline runs; tests live in `tests/` only.
* Canonical verification: `pytest -q && ruff check . && ruff format --check . && mypy tantra_examples && make check`.
