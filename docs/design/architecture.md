# `tantra-examples` — Architecture

**Bounded context**: Examples (Tier 6D) — the reference learning path for the Tantra
Labs ecosystem.
**Language**: Python 3.11+
**Primary responsibility**: canonical, deterministic, offline-runnable tutorials and
reference scripts for Indian equities, NSE/NFO options microstructure, factor models,
walk-forward optimization (WFO), and the autonomous AI research loop.

> History note: this repo was ported from the former `honba-examples` source. The
> completed migration is recorded in [`implementation-record.md`](implementation-record.md)
> and the file-by-file provenance in [`code-migration-map.md`](code-migration-map.md).

---

## 1. Repository Layout (4-Zone Clean Package)

```
tantra-examples/
├── tantra_examples/   # Zone 1: shared harness (app layer; no kernel mirror)
├── examples/          # Zone 2: numbered runnable scripts (flat 01–15 + 13 topic dirs)
├── tests/             # Zone 3: regression tests (unit / integration / snapshots)
└── docs/              # Zone 4: architecture, gaps, plans, reference
```

### Zone 1 — `tantra_examples/` (application harness)

The public package is what every example imports. It has four layers:

| Layer | Paths | Role |
|---|---|---|
| Public API | `__init__.py`, `_compat.py` | Re-exports `Backtest`, `Bar`, `RSI`, `SMA`, `Trade`, `PerformanceMetrics`, `compute_metrics`, `synthetic_bars`, `trending_bars`, `walk_forward_*`; `VYAAPAAR_AVAILABLE` + exact-`Decimal` fallback (`_compat`) |
| Fresh learning-path world | `data.py`, `sdk.py`, `metrics.py`, `backtest.py` (fresh `Backtest`), `walkforward.py` | Deterministic **exact-`Decimal`** bar generation, streaming SMA/RSI, performance metrics, a signal-function backtester, and walk-forward windows |
| Ported harness helpers | `base.py`, `artifact.py`, `bars.py`, `output.py`, `display_style.py`, `jsonable.py`, `cli.py`, `screener_cli.py`, `catalog.py`, `settlement.py`, `sip*.py`, `replay_report.py`, `synthetic.py`, `universe_lists.py` | CLI plumbing (`TantraExample` base), OHLC aggregation, print/stream formatting, deterministic JSON, strategy-catalog loading, settlement resolution, SIP engine, replay reporting |
| Harness & engines | `harness/` (app harness; renamed from `_kernel`, plan 0003), `pipeline/`, `screening/`, `ewr/`, `options/`, `optimizer/`, `ai_replay/` | Application-layer example harness (the kernel-verbatim mirror was dismantled with gaps 0002–0008), composable pipeline DSL, point-in-time screeners, equal-weight rebalancer, options microstructure, optimizer/analytics engines, AI-replay journal |

### Zone 2 — `examples/` (the numbered journey)

- **Flat foundational path** — `examples/01_loading_data.py` … `examples/15_fama_macbeth_factor_regression.py`.
- **13 topic directories** — `basic/`, `candles/`, `storage/`, `universes/`, `strategies/`,
  `backtesting/`, `optimizer/`, `screening/`, `mutual_funds/`, `options/`, `stocksharp/`,
  `ai_research/`, `production/` (94 numbered topic scripts).
- Every numbered script carries a `Pitfalls::` docstring section (enforced by
  `tests/unit/test_pitfalls_sections.py`) and is covered by a regression test in `tests/unit/`.

### Zone 3 — `tests/`

All tests live in `tests/`, parallel to the package (STRICTLY no inline tests in
production modules):

```
tests/
├── unit/           # 124 per-example + helper test files
├── integration/    # 5 cross-module tests (alpha30 parity, LLM decision, pipeline chaining, run-chain)
├── snapshots/      # backtest_parity_golden.json, output_report.txt
└── conftest.py     # load_example fixture (loads numbered scripts by file path)
```

### Zone 4 — `docs/`

- `design/` — this architecture, the implementation record, the code-migration map.
- `gaps/` — open gaps (mirror/stub surface the wheel/owner repos must ship).
- `plans/` — plan index (implemented plans recorded with their closing commits).
- `reference/` — concept reference docs (DSR/PBO, WFO efficiency, options microstructure,
  multibagger screening research, pipeline chaining, refactor plan).

---

## 2. One Decimal World, One Harness

`tantra-examples` now runs entirely on the wheel's Decimal-canonical domain; the second,
kernel-verbatim float world that once lived in `_kernel/` was dismantled when gaps
0002–0008 closed, and the shared harness that remained was renamed
`tantra_examples/harness/` (plan 0003, root plan 0006 Thrust B):

1. **Fresh Decimal world** (learning path canonical):
   - `data.Bar` — frozen `Decimal` OHLCV bar (`open/high/low/close` are `Decimal`,
     `high >= low` validated at construction).
   - `data.synthetic_bars` / `data.trending_bars` — deterministic generators that step in
     **integer paise** (`random.randint`), so no `float` ever represents a price.
   - `sdk.SMA` / `sdk.RSI` — compact streaming indicators over `Decimal`.
   - `metrics` — exact `Decimal` Sharpe/Sortino/Calmar/drawdown/expectancy/win-rate.
   - `backtest.Backtest` — signal-function backtester over fresh bars.
2. **Wheel domain world** — the kernel-verbatim float mirror (`_kernel/`, gaps 0002–0008)
   was fully dismantled (2026-11-15): every domain type now comes from the `tantra`
   wheel (bar/instrument/money/order/position/tick/trade, indicators, `tantra.base`,
   `tantra.declarative`, `tantra.portfolio_strategy`, `tantra.adapters`,
   `tantra.backtest.session`, …), Decimal-canonical throughout. The mirror's only
   survivors — the shared example harness — were renamed to `tantra_examples/harness/`
   under plan 0003 (root plan 0006 Thrust B).

The `_compat.D` alias lets harness code write `Decimal`-polymorphic math that falls back
to pure `decimal.Decimal` when the `tantra` wheel is absent.

---

## 3. Harness Module Map

| Module | Responsibility |
|---|---|
| `base.py` | `TantraExample` base class: common CLI args (`--universe`, `--exchange`, `--start/--end`, `--initial-capital`, `--warmup-days`, `--out-dir`, `--data-dir`, `--format/--width`), lazy `ParquetBarStore` at `find_data_root(REPO_ROOT)`, `load_universe` / `load_bars` / `load_bars_with_warmup`, `run()` + `main()` entry points. |
| `artifact.py` | `bars_digest` (deterministic SHA-256 over bars), `resolve_window`, `write_json_report`. |
| `bars.py` | OHLC aggregation/bucketing to higher timeframes (`aggregate`, `bucket_start`, `timeframe_seconds`); UTC buckets, `ts` = first bar in bucket. |
| `catalog.py` | `load_named` / `strategies_catalog_dir` / `load_catalog_tool` — resolves the `tantra-strategies` catalog (via `tantra_examples.harness.loader`) without fragile sibling paths. |
| `cli.py` | `make_parser`, `add_out_arg`, `emit_json`, `run_example`, and the `VYAAPAAR_EXAMPLES_ALLOW_LIVE_ORDERS` paper-only guard (`require_paper_adapter`). |
| `screener_cli.py` | `ScreenerCLIExample` — stream-friendly screener CLI base (`table/json/csv/symbols/plain` formats) composable in Unix pipes. |
| `output.py` / `display_style.py` | One place every example prints through: `add_output_args`/`resolve_output`, table/JSON/CSV/plain renderers, Indian-money formatting (best-effort `tantra.utils.format` try-import). |
| `jsonable.py` | Deterministic JSON image of domain values (enums by value, sets sorted, ISO dates). |
| `settlement.py` | Settlement-cycle resolution: CLI > config > market default; kernel-mirrored NSE T+2 (before 2023-01-27) / T+1 (from then) schedule. |
| `sip.py` / `sip_plan.py` / `sip_report.py` | Portfolio SIP backtest engine (XIRR bisection, lump sum + monthly installments), single-instrument SIP helpers (Newton-Raphson XIRR), SIP report emitter. |
| `replay_report.py` | Replays a strategy over bars via `tantra_examples.harness.testing.replay` and packages the JSON report. |
| `universe_lists.py` | Nifty 50 / Nifty200 Alpha 30 / Bank Nifty universe lists and `resolve_universe`; mirrored kernel universe surface (gap 0006). |
| `quant.py` | Exact-`Decimal` stats + linear algebra (`returns`, `mean`, `std_dev`, `covariance_matrix`, `solve_linear_system`, `bs_greeks`, `deflated_sharpe`, `pbo` …) mirroring the Rust quant engines (examples 12–15). |
| `amfi.py` | AMFI `NAVAll.txt` parser (`parse_navall`, `nav_bars`, `NavRow`, `NavSkip`) — gap 0003 stand-in. |
| `bhavcopy.py` | NSE EOD bhavcopy dialect-sniffing parser (UDiFF / Sec Bhavdata / legacy) — gap 0003 stand-in. |
| `fake_llm.py` / `decision_guard.py` | `LlmPort` + `ScriptedFakeLlm` (deterministic scripted LLM), and the fail-closed reduce-only guard wrapping the mirrored kernel LLM-decision core. |
| `_compat.py` | Optional `tantra` wheel import + `Decimal` fallback (`D`), `VYAAPAAR_AVAILABLE`. |

### Subpackages

| Subpackage | Responsibility |
|---|---|
| `pipeline/` | Composable in-code strategy pipeline DSL (`ScreenerStep >> Filter >> Sizer >> Harness` via `>>` / `|`): screeners (multibagger/value/dividend), filters (fundamental quality, market regime, liquidity), signals, sizing (fixed SIP / equal-weight / inverse-vol), execution harnesses, stream I/O, manifests. |
| `screening/` | Point-in-time screener engine over the Parquet catalog + `fundamentals.duckdb` (multibagger, value & dividend, Graham, net-net, mutual-funds, swing A+ setups) + path discovery (`VYAAPAAR_DATA_DIR` seam, gap 0003). |
| `ewr/` | Equal-weight rebalancing simulator (`simulate`, `rebalance_orders`, sizing, schedule, reporting) over a shared cash pool with T+1/T+2 settlement and margin tracking. |
| `options/` | Options-microstructure helpers: option-premium STT on sell, ICCL T+1 settlement, Greek risk bounds. SEBI freeze-limit slicing lives in the wheel (`tantra.sizing`, ex 0005 closed). |
| `optimizer/` | Removed 2026-11-15 (ex 0001 closed): Pareto-frontier helpers moved to `tantra.optimizer` and the `algo_analytics` engine moved to `tantra.algo_analytics` in the wheel. |
| `ai_replay/` | SHA-256 prompt cache + Journal v1 NDJSON decision-replay helpers (`PromptCache`, `verify_journal`). |
| `harness/` | The application-layer example harness (renamed from `_kernel` under plan 0003 / root plan 0006 Thrust B), detailed in §5. |

---

## 4. Event Pipeline & Determinism

Tantra's canonical event pipeline (market feed → strategy → risk → execution → fills →
OMS) is exercised by the examples through the harness and the wheel session engine:
`tantra_examples.harness.runner.StrategyRunner` + `tantra.backtest.NextOpenExecution` drive
intents → next-open fills → cash/position/equity accounting. The grafted
`backtest.run_portfolio_backtest` books each order in `CanonicalOrderLedger` (sells
first, then by instrument, so runs are reproducible regardless of `PYTHONHASHSEED`),
trades only inside `[test_start, test_end]`, and reports `fills`, `order_events`,
`equity_curve`, fees and traded notional in integer minor units.

**Determinism invariants**:

- No wall-clock reads in financial math (exceptions: date-window resolution, diagnostic
  fallbacks — `screening/paths.py`, `bhavcopy.py`).
- Synthetic prices are generated in integer paise; exact `Decimal` throughout.
- Replaying identical timestamped events produces identical state (parity pinned by
  `tests/snapshots/backtest_parity_golden.json` and `test_backtest_parity.py`).
- LLM flows use `ScriptedFakeLlm` and SHA-256 prompt caches (`ai_replay`) so they replay
  deterministically offline.

---

## 5. The Application Harness (`tantra_examples/harness/`)

The kernel-verbatim mirror described in earlier revisions of this document was fully
dismantled when gaps 0002–0008 closed (2026-11-15): the wheel now exposes the complete
Decimal-canonical domain surface (`tantra.bar`, `tantra.instrument`, `tantra.money`,
`tantra.order`, `tantra.portfolio`, `tantra.position`, `tantra.tick`, `tantra.trade`,
`tantra.base`, `tantra.indicators`, `tantra.declarative`, `tantra.portfolio_strategy`,
`tantra.adapters`, `tantra.backtest.session`, …) and every mirror file was deleted. See
[`docs/gaps/0006-tantra-wheel-kernel-domain-surface.md`](../gaps/0006-tantra-wheel-kernel-domain-surface.md).

The only files that survived the dismantling are the nine application-harness modules,
renamed from `_kernel/` to `tantra_examples/harness/` under plan 0003 (root plan 0006
Thrust B). The harness is built entirely on the wheel:

| Module | Role |
|---|---|
| `config.py` | `StrategyConfig` (declared strategy parameters). |
| `loader.py` | Strategy-catalog resolution: `find_catalog`, `load_catalog_strategy`, `load_named`, `load_strategy`, `resolve_strategy_version`, `CatalogError`. |
| `log.py` | Event logging: `register_event`, `setup_event_logging`, `EventFilter` (`python -m tantra_examples.harness.log`). |
| `manifest.py` | Strategy manifests: `StrategyManifest`, `ParameterSpec`, `Subscriptions`, `TimeframeSpec`, `Universe`, `WarmupBars`, `STRATEGY_API_VERSION`, param/sweep/trial-grid schemas. |
| `ports.py` | Domain ports: `BarStore`, `MarketDataProvider`, `validate_bar`. |
| `runner.py` | `StrategyRunner` (intent → fill), `RunResult`, `SubmittedIntent`/`SuppressedIntent`, order/intent rejections. |
| `service.py` | `DataService` (bar-store-backed market-data service). |
| `testing.py` | `replay`, `ReplayResult` (bar-close-fill harness used by the examples). |

`tantra_examples/harness/__init__.py` re-exports only these harness names; the wheel
domain surface it once re-exported is now imported directly from `tantra.*`.

---

## 6. Architecture Invariants

1. **Offline & deterministic by default** — every example runs out of the box on
   synthetic/fixture data with `ScriptedFakeLlm`; no live credentials, no network.
2. **Strict zero-floats in financial math** — prices, quantities and fees are
   `decimal.Decimal`; synthetic prices are generated in integer paise. Documented
   exceptions: Black-Scholes internals (example 13) and grafted `metrics.py` statistics.
3. **Parallel test directory rule** — every `examples/.../NN_*.py` has a regression test
   in `tests/unit/`; no inline `test_*` in production modules.
4. **Mandatory `Pitfalls::` docstring section** on every numbered script.
5. **No fragile sibling paths** — examples import installed packages only
   (`test_polyrepo_decoupling.py` enforces zero `../tantra-*` sys.path mutation).

---

## 7. Verification Gates

```bash
# From the repository root
pytest -q                 # unit + integration + snapshots
ruff check .
ruff format --check .
mypy tantra_examples      # type-clean
make check                # lint + format-check + tests
```

See [`implementation-record.md`](implementation-record.md) for the recorded gate status.
