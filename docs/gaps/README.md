# Gap Index — `tantra-examples`

Per workspace rule `.agents/rules/gap-tracking.md`:

- **Gaps** (`docs/gaps/XXXX-*.md`): individual missing features / stubs / mirrors /
  hardcoded stand-ins.
- **Plans** (`docs/plans/XXXX-*.md`): collections of gaps.
- Numbering is per-repo, sequential, never reused.

Dismantled from the former `docs/roadmap/` directory: completed milestones now live in
[`docs/design/implementation-record.md`](../design/implementation-record.md) and the
file mapping in [`docs/design/code-migration-map.md`](../design/code-migration-map.md);
the remaining work is enumerated below.

Every gap names the owning repo so that when the owning surface ships, closing the gap
here means deleting the mirrored code and re-pointing consumers.

## Open Gaps

| # | Slug | Symptom | Owning repo | Status |
| :--- | :--- | :--- | :--- | :--- |
| [0002](0002-tantra-wheel-ai-provider-surface.md) | tantra-wheel-ai-provider-surface | `honba.ai.{ask,decision,llm.provider,autoresearch}` have no wheel equivalent → `_kernel/ai/` mirror, `fake_llm.py`, `decision_guard.py`, `screening/nl_support.py`; `02/04/05/07_autoresearch_loop` design-only (pytest.skip) | `tantra-agent` (research loop, llm adapters) / `tantra-ffi` | open — blocked |
| [0004](0004-tantra-wheel-display-universes-client.md) | tantra-wheel-display-universes-client | `honba.display`, `honba.markets.india.universes`, `honba.client`, `honba.cli.data`, India cost/settlement pack → mirrors in `display_style.py` / `universe_lists.py` / `cli.py` / `screener_cli.py` / `pipeline/io.py` / `options/*` / `_kernel.markets.india` / `_kernel.cli` | `tantra-ffi` | open — blocked |
| [0008](0008-runtime-session-surface.md) | runtime-session-surface | No wheel session orchestrator for real-data runs (next-open fills, NSE costs, T+1 settlement) → `_kernel/session.py` protocol-only stub; `Tantra.backtest` raises `NotImplementedError` on purpose | `tantra-runtime` (Strategy Tester session) / `tantra-ffi` (wheel surface) | open — blocked |

## Closed Gaps

| # | Title | Closed In |
| :--- | :--- | :--- |
| 0001 | tantra-wheel-algo-analytics-surface — wheel `tantra.algo_analytics` / `tantra.quant` / `tantra.optimizer` shipped; mirror (`optimizer/algo_analytics/` + `quant.py`) deleted; consumers retargeted | 2026-11-15 (T9.3; tantra-ffi `d79d31b` + `6ac14dd`, tantra-examples closure) |
| 0003 | tantra-data-nav-loaders — `tantra_data.loaders.{amfi,nse,yfinance}` + `domain.quantity` shipped; wheel `tantra.screener` (catalog/coverage) shipped; `_kernel/data/`+`_kernel/screener/`+`amfi.py`+`bhavcopy.py` deleted; consumers retargeted; `VYAAPAAR_DATA_DIR` offline seam kept (real catalog absent from CI) | 2026-11-15 (ex 0003 closure; tantra-data + tantra-ffi + tantra-examples) |
| 0005 | tantra-exec-freeze-slicer-mirror — wheel `tantra.sizing` freeze-slicing (`freeze_limit_qty`/`slice_order`/`verify_slices`) shipped; `options/__init__.py` mirror removed; consumers retargeted | 2026-11-15 (T9.7; tantra-ffi `d79d31b`, tantra-examples closure) |
| 0006 | tantra-wheel-kernel-domain-surface — the Decimal-canonical wheel kernel-domain layer shipped (money/position/trade/instrument/entities, bar, tick, order, order_state, execution, indicators, base/context, declarative, portfolio_strategy, wire, store, backtest sims); the 166-file `_kernel` mirror's kernel-domain portion deleted; every `_kernel.*` consumer retargeted to the wheel; `[[tool.mypy.overrides]]` dropped | 2026-11-15 (ex 0006 closure; tantra-ffi wheel commits, tantra-examples closure `2684d34` etc.) |
| 0007 | tantra-adapters-framework-surface — wheel `tantra.adapters` shipped; `_kernel/adapters/` (13 modules) deleted; consumers retargeted | 2026-11-15 (ex 0007 closure; tantra-ffi + tantra-examples) |

Status values: `open` (mirror/stub is live in this repo; filing doc exists) ·
`closed` (owner shipped; the gap doc is deleted with the mirror's removal — see the
closing commit).

As of 2026-11-15, the 8-gap dependency cascade rooted in the 166-file `_kernel` mirror is
resolved: the **root (0006) is closed** — the wheel ships the Decimal-canonical kernel
domain and every `_kernel.*` consumer is retargeted to it. The remaining `_kernel/` files
are the other gaps' mirrors (0002 `ai/`, 0004 `markets/india/`+`cli/`, 0008 `session.py`)
plus the shared harness (`runner`, `risk`, `testing`, `portfolio`, …) — all now built on
the wheel, with the cascade root unblocked. **Ownership (ex 0003)**: the screener
catalog/coverage surface landed in the **wheel** (`tantra.screener`, tantra-ffi) because
`tantra.ai` (gap 0002) needs it without a `tantra_data` dependency; the AMFI/NSE loaders and
the Decimal quantity parser landed in **tantra-data** (`tantra_data.loaders.*` +
`tantra_data.domain.quantity`).

Per gap doc template: status · what is stubbed/mirrored · why · how to close it.
