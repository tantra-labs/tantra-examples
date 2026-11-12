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
├── tantra_examples/   # Zone 1: shared harness + ported kernel mirror
├── examples/          # Zone 2: numbered runnable scripts (flat 01–15 + 13 topic dirs)
├── tests/             # Zone 3: regression tests (unit / integration / snapshots)
└── docs/              # Zone 4: architecture, gaps, plans, reference
```

### Zone 1 — `tantra_examples/` (harness + kernel mirror)

The public package is what every example imports. It has four layers:

| Layer | Paths | Role |
|---|---|---|
| Public API | `__init__.py`, `_compat.py` | Re-exports `Backtest`, `Bar`, `RSI`, `SMA`, `Trade`, `PerformanceMetrics`, `compute_metrics`, `synthetic_bars`, `trending_bars`, `walk_forward_*`; `VYAAPAAR_AVAILABLE` + exact-`Decimal` fallback (`_compat`) |
| Fresh learning-path world | `data.py`, `sdk.py`, `metrics.py`, `backtest.py` (fresh `Backtest`), `walkforward.py` | Deterministic **exact-`Decimal`** bar generation, streaming SMA/RSI, performance metrics, a signal-function backtester, and walk-forward windows |
| Ported harness helpers | `base.py`, `artifact.py`, `bars.py`, `output.py`, `display_style.py`, `jsonable.py`, `cli.py`, `screener_cli.py`, `catalog.py`, `settlement.py`, `sip*.py`, `replay_report.py`, `synthetic.py`, `universe_lists.py` | CLI plumbing (`TantraExample` base), OHLC aggregation, print/stream formatting, deterministic JSON, strategy-catalog loading, settlement resolution, SIP engine, replay reporting |
| Mirrors & engines | `_kernel/`, `pipeline/`, `screening/`, `ewr/`, `options/`, `optimizer/`, `ai_replay/`, `amfi.py`, `bhavcopy.py`, `quant.py`, `fake_llm.py`, `decision_guard.py` | Kernel-verbatim mirrors (gaps 0002–0008), composable pipeline DSL, point-in-time screeners, equal-weight rebalancer, options microstructure, optimizer/analytics engines, AI-replay journal |

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

## 2. The Two Worlds

`tantra-examples` deliberately contains **two coexisting bar/type worlds**, joined at
the harness boundary:

1. **Fresh Decimal world** (learning path canonical):
   - `data.Bar` — frozen `Decimal` OHLCV bar (`open/high/low/close` are `Decimal`,
     `high >= low` validated at construction).
   - `data.synthetic_bars` / `data.trending_bars` — deterministic generators that step in
     **integer paise** (`random.randint`), so no `float` ever represents a price.
   - `sdk.SMA` / `sdk.RSI` — compact streaming indicators over `Decimal`.
   - `metrics` — exact `Decimal` Sharpe/Sortino/Calmar/drawdown/expectancy/win-rate.
   - `backtest.Backtest` — signal-function backtester over fresh bars.
2. **Kernel mirror world** (`_kernel/`, gaps 0002–0008):
   - `_kernel.bar.Bar` / `InstrumentId` / `Money` / `OrderIntent` / `OrderSide` … — the
     ported kernel-domain types. This is the float-domain world the engine uses, kept
     byte-verbatim from the owning engine so golden parity tests pin its behaviour.
   - `_kernel.backtest.simulated` / `runner.py` — the deterministic simulator and
     `StrategyRunner` the grafted `backtest.run_portfolio_backtest` drives.
   - `_kernel.indicators/` (87 files) — the ported indicator registry and families
     (moving_average, trend, momentum, volatility, volume, breadth, statistical,
     support_resistance).
   - `_kernel.adapters/` (13 files, gap 0007) — the adapter framework mirror
     (registry, capabilities, contract, `FakeAdapter`, session, rate-limit, secrets).
   - `_kernel.ai/`, `_kernel.wire/`, `_kernel.markets/india/`, `_kernel.portfolio_strategy/`,
     `_kernel.screener/`, `_kernel.data/`, `_kernel.cli/` — further kernel mirrors.

The `_compat.D` alias lets harness code write `Decimal`-polymorphic math that falls back
to pure `decimal.Decimal` when the `tantra` wheel is absent.

---

## 3. Harness Module Map

| Module | Responsibility |
|---|---|
| `base.py` | `TantraExample` base class: common CLI args (`--universe`, `--exchange`, `--start/--end`, `--initial-capital`, `--warmup-days`, `--out-dir`, `--data-dir`, `--format/--width`), lazy `ParquetBarStore` at `find_data_root(REPO_ROOT)`, `load_universe` / `load_bars` / `load_bars_with_warmup`, `run()` + `main()` entry points. |
| `artifact.py` | `bars_digest` (deterministic SHA-256 over bars), `resolve_window`, `write_json_report`. |
| `bars.py` | OHLC aggregation/bucketing to higher timeframes (`aggregate`, `bucket_start`, `timeframe_seconds`); UTC buckets, `ts` = first bar in bucket. |
| `catalog.py` | `load_named` / `strategies_catalog_dir` / `load_catalog_tool` — resolves the `tantra-strategies` catalog (via `_kernel.loader`) without fragile sibling paths. |
| `cli.py` | `make_parser`, `add_out_arg`, `emit_json`, `run_example`, and the `VYAAPAAR_EXAMPLES_ALLOW_LIVE_ORDERS` paper-only guard (`require_paper_adapter`). |
| `screener_cli.py` | `ScreenerCLIExample` — stream-friendly screener CLI base (`table/json/csv/symbols/plain` formats) composable in Unix pipes. |
| `output.py` / `display_style.py` | One place every example prints through: `add_output_args`/`resolve_output`, table/JSON/CSV/plain renderers, Indian-money formatting (best-effort `tantra.utils.format` try-import). |
| `jsonable.py` | Deterministic JSON image of domain values (enums by value, sets sorted, ISO dates). |
| `settlement.py` | Settlement-cycle resolution: CLI > config > market default; kernel-mirrored NSE T+2 (before 2023-01-27) / T+1 (from then) schedule. |
| `sip.py` / `sip_plan.py` / `sip_report.py` | Portfolio SIP backtest engine (XIRR bisection, lump sum + monthly installments), single-instrument SIP helpers (Newton-Raphson XIRR), SIP report emitter. |
| `replay_report.py` | Replays a strategy over bars via `_kernel.testing.replay` and packages the JSON report. |
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
| `options/` | Options-microstructure helpers: option-premium STT on sell, ICCL T+1 settlement, SEBI freeze-limit read + `slice_order` / `verify_slices` (gap 0005), Greek risk bounds. |
| `optimizer/` | Pareto-frontier extraction/plotting + `algo_analytics/` engine mirrors (gap 0001): `walk_forward`, `folds`, `monte_carlo`, `plateau`, `deflated_sharpe`, `metrics` (Sharpe/Sortino). |
| `ai_replay/` | SHA-256 prompt cache + Journal v1 NDJSON decision-replay helpers (`PromptCache`, `verify_journal`). |
| `_kernel/` | The kernel mirror (gaps 0002–0008), detailed in §5. |

---

## 4. Event Pipeline & Determinism

Tantra's canonical event pipeline (market feed → strategy → risk → execution → fills →
OMS) is exercised by the examples through the mirrored kernel:
`_kernel.runner.StrategyRunner` + `_kernel.backtest.simulated.NextOpenExecution` drive
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

## 5. The Kernel Mirror (`_kernel/`, 166 files)

The wheel does not yet expose the kernel-domain surface, so the ported kernel lives
in-repo as `tantra_examples._kernel.*`. Each mirrored file carries a
`# mirror: kernel-verbatim port (gap NNNN)` citation after its docstring, plus
`# mirror accommodation (gap NNNN)` type:ignore comments where the verbatim kernel
assigns dynamic class attributes or typed unions. See
[`docs/gaps/0006-tantra-wheel-kernel-domain-surface.md`](../gaps/0006-tantra-wheel-kernel-domain-surface.md).

| Sub-tree | Files | Content |
|---|---|---|
| `_kernel/` root | 33 | `bar`, `instrument`, `order`, `order_state`, `portfolio`, `position`, `trade`, `money`, `coverage`, `store` (Parquet), `service`, `evaluator`, `calendar`, `base` (Strategy/Parameter), `config`, `manifest`, `loader`, `context`, `entities`, `native` (pinned constants), `testing` (replay), `runner`, `risk`, `execution`, `declarative`, `sizing`, `session`, `greeks`, `option`, `ports`, `log`, `tick` |
| `_kernel/adapters/` | 13 | adapter framework mirror (gap 0007) |
| `_kernel/ai/` | 6 | ask / decision / knowledge / llm.provider (gap 0002) |
| `_kernel/backtest/` | 5 | `simulated`, `impact`, `l2_sim`, `opening_auction` (gap 0006) |
| `_kernel/indicators/` | 87 | registry + 8 families (gap 0006) |
| `_kernel/markets/india/` | 3 | costs + settlement (gap 0004) |
| `_kernel/portfolio_strategy/` | 10 | tamashii portfolio strategies (gap 0006) |
| `_kernel/screener/` | 2 | catalog + coverage (gap 0002/0003) |
| `_kernel/wire/` | 4 | wire envelope + `SCHEMA_VERSION` check |
| `_kernel/cli/` | 1 | store accessor (gap 0004) |
| `_kernel/data/` | 1 | `Quantity` parse (gap 0003) |

Pinned constants (`_kernel/native.py`): `SCHEMA_VERSION = 8`, `API_VERSION = "v1"`,
`STRATEGY_API_VERSION = "1.0.0"`, currency-minor-units table — sourced from the owning
engine's Rust constants; delete with the mirror when the wheel ships the surface.

---

## 6. Architecture Invariants

1. **Offline & deterministic by default** — every example runs out of the box on
   synthetic/fixture data with `ScriptedFakeLlm`; no live credentials, no network.
2. **Strict zero-floats in financial math** — prices, quantities and fees are
   `decimal.Decimal`; synthetic prices are generated in integer paise. Documented
   exceptions: Black-Scholes internals (example 13), grafted `metrics.py` statistics,
   and the kernel-mirror float domain (gap 0006).
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
