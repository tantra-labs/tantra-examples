# `tantra-examples` — Inter-Agent Handoff

## Latest Batch
* **Plan 0004 IMPLEMENTED — T15 COMPLETE (2026-11-16, all six milestones)**: the data-
  provisioning service landed in `tantra_examples/provision/` across four commits: `f76428b`
  (M1 — layout/contracts/dummy + openapi.json + `synthetic_lakehouse.py` re-export shim),
  `5cd3897` (M2+M3 — seam `choose_mode`/`ensure_data_root`, conftest `write_symbol` fold,
  seeded/truly-random GBM `monte_carlo.py`), `7b98b78` (M4+M5 — download runner over
  `tantra_data.cli.ingest_*`, FastAPI `server.py` + httpx `client.py`), `36e468f` (M6 — per-test
  duckdb parquet writers folded onto the canonical writer; seam `__main__` runtime prompt).
  **Gate: `tests/unit` = 1014 passed / 1 skipped** (the skip is honest —
  `tantra_data.store.mutual_funds` gap 0023); ruff check + format clean; mypy clean on
  `provision/`; `python -m tantra_examples.provision.seam` is the interactive runtime prompt.
  Plan 0004 → **Implemented** (index moved; doc retained per 0003 precedent).
* **All 51 unit-suite skips fixed (2026-11-16) — `tests/unit` now 967 passed / 1 skipped** (was
  916 passed / 51 skipped). The 50 fixable skips fell into 4 roots: (1) missing optional deps
  (`numpy`+`scipy` installed into the wheel venv; `test_04_portfolio_optimization` also needed a
  Decimal-quantize fix in `tantra_data.loaders.amfi.nav_bars` and a float-cast at the numpy
  boundary in `examples/mutual_funds/04_portfolio_optimization.py`); (2) `test_screening_import`
  reworked to exercise the missing-`tantra_data` path via a `sys.meta_path` blocker; (3) the
  tantra-strategies catalog was missing `registry.json` + `tools/validate_chain.py` — shipped in
  the provider repo (see tantra-strategies HANDOFF) un-skipping the 28 pipeline chain/manifest
  tests; (4) the 1D NSE catalog tests got a deterministic synthetic lakehouse —
  `tests/unit/synthetic_lakehouse.py` (price catalog + `fundamentals.duckdb`) behind the
  `VYAAPAAR_DATA_DIR` seam via a shared `_real_catalog` fixture in `tests/unit/conftest.py`,
  un-skipping test_08/09/10 + test_screening_cli. Also fixed a wheel-API regression in
  `examples/production/06_multi_broker_dispatch.py` (paper mocks now registered unconditionally
  `replace=True`; `available_adapters` import dropped) and re-gated two integration suites on
  their true prerequisites (test_07 runnable-catalog strategy; test_run_chain 1D data catalog).
  **1 remaining skip** is honest: `test_mutual_fund_screener_execution` — the
  `tantra_data.store.mutual_funds` store surface doesn't exist yet (filed tantra-data gap 0023).
  Gates: `ruff check` + `ruff format --check` clean; integration green.
* **T13 COMPLETE (2026-11-16, plan 0003 / root plan 0006 T13.6–T13.7)**: renamed the remaining
  harness `tantra_examples/_kernel/` → `tantra_examples/harness/` via `git mv` (history preserved
  for all 9 files). `harness/__init__.py` rewritten as a pure app-layer facade (only harness names:
  `StrategyConfig`, `Catalog*`/loader, `EventFilter`/log, `StrategyManifest`/manifest,
  `BarStore`/ports, `StrategyRunner`/runner, `DataService`, `replay`/testing — no wheel domain
  re-exports). Every `tantra_examples._kernel.*` import retargeted (harness internal, `backtest.py`,
  `sip_plan.py`, `replay_report.py`, `catalog.py`, 27 test files, ~25 example scripts); the
  `_kernel` name is **deleted repo-wide** (Step 6 grep: 0 matches in `*.py`). Docs swept:
  `architecture.md` (§2 “one world”, §3 rows, §4, §5 rewritten as “The Application Harness”),
  `code-migration-map.md` + `gap-cascade-kernel-mirror.md` + `docs/gaps|plans/README.md` note the
  rename, and the strategies/backtesting README code snippets now import from `tantra.base`,
  `tantra.indicators`, `tantra_examples.harness.testing`. Plan 0003 **Implemented** (index updated;
  root plan 0006 closed). **Gate (T13.7)**: `tests/unit` = **909 passed / 51 skipped / 6 pre-existing
  failures** — the 6 `test_06_multi_broker_dispatch` failures reproduce **identically on pre-T13
  HEAD `1d89fd9`** (verified in a detached worktree) and are environmental, not from T13: the
  installed `tantra_adapters` package exposes real broker entry points (`zerodha`/`angelone`/…), so
  the example's `register_adapter("zerodha", lambda **kwargs: PaperBrokerAdapter(...))` fallback is
  skipped and `resolve_adapter(broker, config=…)` calls the real adapter's constructor, which
  rejects the `config` kwarg. Run-order dependent (can pass if an earlier test registers a
  compatible factory). ruff `check` + `format --check` clean; 6 example import-smokes pass. Commits
  `25cb5df` (Thrust A), `1acabfb9` (Thrust B), `3c2e5ae` (docs), `f07f8e1` (`.venv` gitignore),
  all local (not pushed). Thrust A (the wheel lift that deleted the six domain modules
  `_kernel/{portfolio,risk,greeks,option,evaluator,calendar}.py`) was already complete before this
  batch; the facade now exposes no wheel names at all.
* **Unit suite fully green (2026-11-15)**: all 73 pre-existing float-rooted failures + 3 errors fixed
  (tests/unit: **916 passed / 51 skipped**, exit 0; wheel suite in tantra-ffi: **464 passed**). Root
  cause throughout: examples/tests mixed Python `float` with the Decimal-canonical wheel
  (`tantra.bar.Bar`, `tantra.trade.Trade`, greeks all carry `decimal.Decimal`). Fixes, all
  zero-floats-compliant:
  - **Harness**: `tantra_examples/metrics.fills_equity_curve` is now exact Decimal;
    `tantra_examples/screening/nl_support.safe_eval_predicate` is Decimal-canonical (row values +
    float predicate constants coerced via a `_d` AST rewrite; `Decimal` imported).
  - **Examples**: `02_with_indicators`, `02_sip_backtest`, `05_expiry_day_strategy`,
    `06_nifty_920_straddle`, `08_iron_condor_hedging`, `01_paper_trading`, `03_multi_account`,
    `06_multi_broker_dispatch` — float literals → `Decimal(str(...))` (import `from decimal import Decimal`);
    `04_place_order_paper.main` raw `json.dumps` → `default=str`.
  - **Tests** (the bulk): assertions compare the actual returned type — jsonable decimal strings
    (`'2515.0'`), raw `Decimal`, or `int` — never a mismatched float literal; determinism tests add
    `default=str`; `test_backtest` marks-to-minor ×100; `test_screening_cli` MF-screener test uses the
    `_real_catalog` fixture (skips offline); **`tests/snapshots/backtest_parity_golden.json`
    regenerated** (stale pin drifted 0.01 INR / 0.03 Sharpe vs the current Decimal-canonical backtest).
  - 4 pre-existing unformatted files (08_sip_buy_and_hold, 05_multi_instrument, 14_partial_fill_handling,
    test_06_equal_weight_rebalance) run through `ruff format`.
  - Gates: `ruff check .` clean, `ruff format --check .` clean, `pytest tests/unit -q` exit 0
    (916 passed / 51 skipped; the only functional skip is the mutual-fund screener needing the real
    1D NSE catalog).
* **T13 PLANNED → Thrust B DONE (2026-11-15 planned, executed 2026-11-16)**: plan
  `docs/plans/0003-tantra-examples-harness-dismantle.md` was filed (Proposed) for the harness
  rename `_kernel/` → `tantra_examples/harness/` (config/loader/log/manifest/ports/runner/service/
  testing), ~60 `_kernel.*` import sites, deleting `_kernel/`, gate + follow-on candidates (root
  plan 0006, Thrust B; T13.6–T13.7). **Executed** — see the top batch entry (commit
  `1acabfb9`); plan 0003 is now **Implemented-pending** (T13 gate sign-off remains).
* **Gap 0008 CLOSED (2026-11-15)**: wheel `tantra.backtest.session` shipped; `_kernel/session.py`
  deleted; the `_kernel/` mirror is fully dismantled — only the shared harness remains.
* **Gap 0008 CLOSED (2026-11-15, ex 0008 closure — the last gap; all 8 closed)** — the
  wheel shipped the session orchestrator (`tantra.backtest.session`, `Tantra.backtest`
  next-open fills, India delivery costs, T+1 settlement; tantra-ffi `2d9214e`) and the
  wheel `algo_analytics` consumers (`monte_carlo`/`plateau`/`walk_forward`) now default
  to it. This repo **deleted `_kernel/session.py`** (the final mirror/stub) and
  retargeted the one docstring reference (`examples/backtesting/01_first_backtest.py`).
  **All 8 gaps (0001–0008) are closed**; the `_kernel` mirror is fully dismantled and
  only the shared example harness remains. Unit suite now fully green (916 passed / 51 skipped —
  see the top entry; all 73 pre-existing float-rooted failures + 3 errors were fixed 2026-11-15).
* **Gap 0002 CLOSED (2026-11-15, ex 0002 closure)** — the wheel shipped `tantra.ai`
  (ask / decision / knowledge / llm.provider; tantra-ffi `4d570b4`). This repo **deleted the
  mirrors** (`_kernel/ai/`, `fake_llm.py`, `decision_guard.py`) and **retargeted every
  consumer** to `tantra.ai.*` (`screening/nl_support.py` retained as the screener harness,
  import retargeted only). The 4 design-only scripts (02/04/05/07) were **un-skipped** and
  now run deterministic demos of the shipped surface (02 research-loop demo, 04 NL→filter
  demo via the `tantra.screener` catalog, 05 + 07 runnable design notes). Unit suite:
  916 passed / 51 skipped (fully green — see the top entry; all failures fixed 2026-11-15).
* **Gap 0004 CLOSED (2026-11-15, ex 0004 closure)** — the wheel shipped `tantra.display`
  + `tantra.markets.india` (costs/settlement) + `tantra.markets.india.universes` +
  `tantra.cli.data` (tantra-ffi `e5f40b3` + `723c9c0`; the latter retargets the wheel's own
  `NamedUniverse` stand-in to `tantra.markets.india.universes`). This repo **deleted the
  mirrors** (`display_style.py`, `universe_lists.py`, `pipeline/io.py`,
  `_kernel/markets/india/`, `_kernel/cli/`) and **retargeted every consumer** to the wheel
  (`tantra.display`, `tantra.markets.india.{costs,settlement,universes}`,
  `tantra.cli.data`); the `_kernel.cli._STORE` global became `tantra_examples.base.get_store`.
  `output.py`/`screener_cli.py`/`cli.py` stay as example-harness modules on top of the wheel
  surfaces (only their imports were retargeted), not kernel mirrors. Unit suite unchanged
  (840 passed / 73 failed / 3 errors / 41 skipped — no new failures).
* **Gap 0003 CLOSED (2026-11-15, ex 0003 closure)** — the owning surfaces shipped:
  `tantra_data.loaders.{amfi,nse,yfinance}` + `tantra_data.domain.quantity` (tantra-data
  `54d5b34`) and the wheel `tantra.screener` catalog/coverage surface (tantra-ffi
  `07b4956`). This repo **deleted the mirrors** (`_kernel/data/`, `_kernel/screener/`,
  `amfi.py`, `bhavcopy.py`) and **retargeted every consumer** to `tantra_data.loaders.*` +
  `tantra.screener` + `tantra_data.parse_quantity` (12 AMFI consumers, the bhavcopy import,
  `_kernel.ai.{ask,knowledge}` catalog imports, `01_llm_research_analyst`, `03_nl_screener`,
  7 test files). The `VYAAPAAR_DATA_DIR` offline seam in `screening/paths.py` is kept (the
  real NSE catalog is absent from CI). Unit suite in the provisioned venv is identical to
  untouched HEAD (840 passed / 73 failed / 3 errors / 41 skipped — no new failures; the +1
  over the pre-provisioning 72 is `test_screening_cli::test_mutual_fund_screener_execution`,
  which now runs instead of skipping because `tantra_data` is installed, and fails on the
  known catalog-absent condition).
* **Gap 0007 CLOSED (2026-11-15, ex 0007 closure)** — wheel `tantra.adapters` shipped
  (tantra-ffi `437eddf5`); `_kernel/adapters/` mirror (13 modules) deleted; 18 consumers
  retargeted; adapters unit tests green. Unit suite now fully green (see top entry).
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
  was the `decision_guard` re-export — both later shipped as wheel `tantra.ai` in the ex 0002
  closure).
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
  / 50 skipped. Status: shipped-mirror deletion complete; the only remaining `_kernel` mirror
  was `session.py` (gap 0008), deleted in the ex 0008 closure — ex 0006 stays open for the
  compiled risk/trading-state surface.
* **Blocker analysis + dependency map**: verified the 8-gap cascade rooted in the 166-file
  `_kernel` mirror (`docs/design/gap-cascade-kernel-mirror.md`); gap 0008 carried
  `open — blocked` status with precise blockers (0002 closed, ex 0002 closure; 0006 closed) —
  now closed in the ex 0008 closure.
* **Gates**: full `pytest` green except one pre-existing environmental failure
  (`test_mutual_fund_screener_execution` needs the 1D NSE catalog on disk); `ruff check` +
  `ruff format --check` clean (incl. pre-existing I001/SIM102 in untouched files fixed).

## Phase / Slice Status
* **Plan 0004 / T15 COMPLETE (2026-11-16)**: `tantra_examples/provision/` shipped — layout,
  contracts, dummy (canonical synthetic source), monte-carlo (seeded/truly-random GBM),
  download (tantra-data CLI delegation), FastAPI server + httpx client, seam runtime prompt,
  openapi.json; per-test parquet writers folded onto the canonical writer; suite 1014/1.
  All six milestones done; plan index moved to Implemented.
* **Honba staged port (plan 0002)** — **ALL 9 STAGES COMPLETE (Stages 0–8)**; recorded Implemented in `docs/plans/README.md` (commit `bbfa692`). Plan doc cleaned up per gap-tracking §4.
* **Docs (this change)**: former `docs/roadmap/` (`roadmap.md` + `migration-verification.md`) dismantled into `docs/design/` (`architecture.md`, `implementation-record.md`, `code-migration-map.md`), `docs/gaps/` (README + 0001–0008 source-verified), and `docs/plans/README.md`; `docs/reference/` concept docs unchanged.
* Full verification gates were green at port close: `pytest -q` (922 passed, 70 skipped), `ruff check .`, `ruff format --check .`, `mypy tantra_examples` (234 files), `make check`.

## Decisions & Discoveries
* **Pytest import mode & test structure**: `pythonpath = ["."]` in `pyproject.toml` + empty `__init__.py` in `tests/`, `tests/unit/`, `tests/integration/` lets `pytest -q` run from the repo root and resolves module-name collisions between unit and integration tests.
* **Kernel mirror is the wheel-missing stand-in**: `tantra_examples/_kernel/` was a 166-file kernel-verbatim mirror (indicators 87, portfolio_strategy 10, adapters 13) cited against gaps 0002–0008. The ex 0006 closure (Wave 5b) deleted the shipped modules and the `[[tool.mypy.overrides]]` block; `SCHEMA_VERSION`/`API_VERSION` now come from the wheel (`tantra.SCHEMA_VERSION`/`tantra.API_VERSION`). The remaining `_kernel` files (calendar/config/evaluator/greeks/loader/log/manifest/option/portfolio/ports/risk/runner/service/testing) were the shared example harness, all built on the wheel — no mirrors remained after the ex 0008 closure deleted `session.py`; under plan 0003 Thrust B (2026-11-16) the surviving harness modules were renamed to `tantra_examples/harness/`.
* **Gap 0004 stream plumbing**: the standalone screener CLIs stream through `screener_cli.py` re-exporting `tantra.cli.data` (`read_symbols`/`to_stream`/`parse_symbols`/`dumps`), not a `stream.py` module.
* **Gap 0005**: only `examples/options/07_large_qty_options_slicer.py` probes optional `tantra_te_slicer`; `examples/stocksharp/02_twap_vwap.py` imports `tantra_examples.options` directly.
* **Pitfalls contract**: flat foundational scripts (15) have 2–3 bullets; topic scripts (94) have 3–6. `test_pitfalls_sections.py` accommodates both.
* **Offline catalog seam**: integration tests that require the multi-GB real Parquet catalog skip when run offline (`VYAAPAAR_DATA_DIR` synthetic fixture seam, kept after the gap 0003 closure).

## Immediate Next Step
* **Plan 0004 / T15 COMPLETE (2026-11-16)** — all six milestones shipped and verified
  (1014 passed / 1 skipped). Remaining workspace-level follow-ons (recorded, NOT required):
  1. **tantra-data gap 0023** — `tantra_data.store.mutual_funds` store surface; when shipped,
     wire `provision`'s `mutual_funds` dataset + un-skip
     `test_mutual_fund_screener_execution` (the 1 honest skip).
  2. Optional: fundamentals randomizer for `monte_carlo` (currently deterministic via
     `build_fundamentals`); a `provision` runtime prompt wired into the numbered examples
     (seam `__main__` is the entry point); `download` progress/cancellation between symbols.
  Otherwise example-side maintenance (keep every numbered script runnable and its
  `tests/unit/` regression green) or whatever the orchestrator assigns next.
* All 9 stages of the `honba-examples` port are complete and verified; docs batch committed.
* All 8 gaps (0001–0008) are closed; the `_kernel` mirror is fully dismantled and the harness was
  renamed to `tantra_examples/harness/` (plan 0003, root plan 0006 Thrust B, commits `25cb5df` +
  `1acabfb9`, 2026-11-16). **T13 complete — plan 0003 Implemented, root plan 0006 closed.**
  Remaining candidates (recorded, NOT required to close): `harness/runner.py` `StrategyRunner` vs
  the wheel `tantra.backtest.session`; `harness/service.py` `DataService` vs `tantra_data`'s
  service layer; `harness/testing.py` `replay` as a future wheel backtest-replay helper; and the
  end-to-end Decimal conversion of `metrics.fills_equity_curve` + its consumers (conversion must
  ship curve AND consumers together — a partial rework was reverted 2026-11-15). Otherwise
  example-side maintenance (keep every numbered script runnable and its `tests/unit/` regression
  green) or whatever the orchestrator assigns next.

## Operating Invariants
* Zero floats in financial math (documented exceptions: BS internals example 13; grafted `metrics.py` stats). Deterministic offline runs; tests live in `tests/` only.
* Canonical verification: `pytest -q && ruff check . && ruff format --check . && mypy tantra_examples && make check`.
