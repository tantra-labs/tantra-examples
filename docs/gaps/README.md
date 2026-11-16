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

None — all 8 gaps are closed.

## Closed Gaps

| # | Title | Closed In |
| :--- | :--- | :--- |
| 0001 | tantra-wheel-algo-analytics-surface — wheel `tantra.algo_analytics` / `tantra.quant` / `tantra.optimizer` shipped; mirror (`optimizer/algo_analytics/` + `quant.py`) deleted; consumers retargeted | 2026-11-15 (T9.3; tantra-ffi `d79d31b` + `6ac14dd`, tantra-examples closure) |
| 0002 | tantra-wheel-ai-provider-surface — wheel `tantra.ai` (ask/decision/knowledge/llm.provider) shipped; `_kernel/ai/` + `fake_llm.py` + `decision_guard.py` deleted; consumers retargeted; 4 design-only scripts un-skipped; `nl_support.py` retained as screener harness | 2026-11-15 (ex 0002 closure; tantra-ffi + tantra-examples) |
| 0003 | tantra-data-nav-loaders — `tantra_data.loaders.{amfi,nse,yfinance}` + `domain.quantity` shipped; wheel `tantra.screener` (catalog/coverage) shipped; `_kernel/data/`+`_kernel/screener/`+`amfi.py`+`bhavcopy.py` deleted; consumers retargeted; `VYAAPAAR_DATA_DIR` offline seam kept (real catalog absent from CI) | 2026-11-15 (ex 0003 closure; tantra-data + tantra-ffi + tantra-examples) |
| 0004 | tantra-wheel-display-universes-client — wheel `tantra.display` + `tantra.markets.india` (costs/settlement) + `tantra.markets.india.universes` + `tantra.cli.data` shipped; `display_style.py`/`universe_lists.py`/`pipeline/io.py` + `_kernel/markets/india/` + `_kernel/cli/` deleted; consumers retargeted; `tantra.client` (REST) remains a separate future surface (options/* keep the best-effort try-import) | 2026-11-15 (ex 0004 closure; tantra-ffi + tantra-examples) |
| 0005 | tantra-exec-freeze-slicer-mirror — wheel `tantra.sizing` freeze-slicing (`freeze_limit_qty`/`slice_order`/`verify_slices`) shipped; `options/__init__.py` mirror removed; consumers retargeted | 2026-11-15 (T9.7; tantra-ffi `d79d31b`, tantra-examples closure) |
| 0006 | tantra-wheel-kernel-domain-surface — the Decimal-canonical wheel kernel-domain layer shipped (money/position/trade/instrument/entities, bar, tick, order, order_state, execution, indicators, base/context, declarative, portfolio_strategy, wire, store, backtest sims); the 166-file `_kernel` mirror's kernel-domain portion deleted; every `_kernel.*` consumer retargeted to the wheel; `[[tool.mypy.overrides]]` dropped | 2026-11-15 (ex 0006 closure; tantra-ffi wheel commits, tantra-examples closure `2684d34` etc.) |
| 0007 | tantra-adapters-framework-surface — wheel `tantra.adapters` shipped; `_kernel/adapters/` (13 modules) deleted; consumers retargeted | 2026-11-15 (ex 0007 closure; tantra-ffi + tantra-examples) |
| 0008 | runtime-session-surface — wheel `tantra.backtest.session` shipped (`Tantra.backtest` next-open fills, India delivery costs, T+1 settlement); wheel `algo_analytics` retargeted; `_kernel/session.py` deleted | 2026-11-15 (ex 0008 closure; tantra-ffi + tantra-examples) |

Status values: `open` (mirror/stub is live in this repo; filing doc exists) ·
`closed` (owner shipped; the gap doc is deleted with the mirror's removal — see the
closing commit).

As of 2026-11-15, the 8-gap dependency cascade rooted in the 166-file `_kernel` mirror is
resolved: **all 8 gaps are closed** — the `_kernel` mirror is fully dismantled. The
remaining `_kernel/` files were only the shared example harness
(`calendar`, `config`, `evaluator`, `greeks`, `loader`, `log`, `manifest`, `option`,
`portfolio`, `ports`, `risk`, `runner`, `service`, `testing`) — all built on the wheel,
with the cascade root unblocked; the harness survivors were renamed to
`tantra_examples/harness/` under plan 0003 (root plan 0006, T13 Thrust B). **Retained harness (ex 0004)**: `output.py`, `screener_cli.py` and
`cli.py` are example-harness modules that stay on top of the wheel surfaces — only their
imports were retargeted to `tantra.display` / `tantra.cli.data`; they are not kernel
mirrors. **Ownership (ex 0003)**: the screener
catalog/coverage surface landed in the **wheel** (`tantra.screener`, tantra-ffi) because
`tantra.ai` (gap 0002) needs it without a `tantra_data` dependency; the AMFI/NSE loaders and
the Decimal quantity parser landed in **tantra-data** (`tantra_data.loaders.*` +
`tantra_data.domain.quantity`).

Per gap doc template: status · what is stubbed/mirrored · why · how to close it.
