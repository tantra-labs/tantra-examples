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
| [0003](0003-tantra-data-nav-loaders.md) | tantra-data-nav-loaders | `tantra_data` loaders/store/mutual-funds/coverage surface missing → in-repo `amfi.py`, `bhavcopy.py`, `screening/paths.py` (`VYAAPAAR_DATA_DIR` seam) + `_kernel.data`/`_kernel.screener` mirrors | `tantra-data` | open — blocked |
| [0004](0004-tantra-wheel-display-universes-client.md) | tantra-wheel-display-universes-client | `honba.display`, `honba.markets.india.universes`, `honba.client`, `honba.cli.data`, India cost/settlement pack → mirrors in `display_style.py` / `universe_lists.py` / `cli.py` / `screener_cli.py` / `pipeline/io.py` / `options/*` / `_kernel.markets.india` / `_kernel.cli` | `tantra-ffi` | open — blocked |
| [0006](0006-tantra-wheel-kernel-domain-surface.md) | tantra-wheel-kernel-domain-surface | kernel-domain engine surface (types, Strategy contract, manifests/wire, store, evaluator, native attributes, indicator registry, declarative/execution/sizing, portfolio_strategy) absent from the wheel → `_kernel/` mirror (166 files) + `native.py` pins | `tantra-ffi` | open — in progress (Decimal domain-core slice shipped) |
| [0007](0007-tantra-adapters-framework-surface.md) | tantra-adapters-framework-surface | `honba.adapters` framework (contract/registry/capabilities/models/FakeAdapter/session/rate_limit/secrets) absent from the wheel → `_kernel/adapters/` mirror (13 files) | `tantra-adapters` (connector packages) / `tantra-ffi` (wheel namespace) | open — blocked |
| [0008](0008-runtime-session-surface.md) | runtime-session-surface | No wheel session orchestrator for real-data runs (next-open fills, NSE costs, T+1 settlement) → `_kernel/session.py` protocol-only stub; `Tantra.backtest` raises `NotImplementedError` on purpose | `tantra-runtime` (Strategy Tester session) / `tantra-ffi` (wheel surface) | open — blocked |

## Closed Gaps

| # | Title | Closed In |
| :--- | :--- | :--- |
| 0001 | tantra-wheel-algo-analytics-surface — wheel `tantra.algo_analytics` / `tantra.quant` / `tantra.optimizer` shipped; mirror (`optimizer/algo_analytics/` + `quant.py`) deleted; consumers retargeted | 2026-11-15 (T9.3; tantra-ffi `d79d31b` + `6ac14dd`, tantra-examples closure) |
| 0005 | tantra-exec-freeze-slicer-mirror — wheel `tantra.sizing` freeze-slicing (`freeze_limit_qty`/`slice_order`/`verify_slices`) shipped; `options/__init__.py` mirror removed; consumers retargeted | 2026-11-15 (T9.7; tantra-ffi `d79d31b`, tantra-examples closure) |

Status values: `open` (mirror/stub is live in this repo; filing doc exists) ·
`closed` (owner shipped; the gap doc is deleted with the mirror's removal — see the
closing commit).

As of 2026-11-15, the 8-gap dependency cascade rooted in the 166-file `_kernel` mirror is
verified (see [`docs/design/gap-cascade-kernel-mirror.md`](../design/gap-cascade-kernel-mirror.md));
the `_kernel`-independent surfaces (0001 algo_analytics, 0005 freeze-slicer) are **closed** via
the wheel; 0006 is in progress (Decimal domain-core slice shipped); 0002/0003/0004/0007/0008
stay open with blocker analysis per doc.

Per gap doc template: status · what is stubbed/mirrored · why · how to close it.
