# 0003 — Dismantle `_kernel`: Harness Rename + Gate (Thrust B of root plan 0006)

**Status**: Proposed (planning only; no development yet).
**Track**: T13 (rows T13.6–T13.7) · **Root master plan**: `docs/plans/0006-dismantle-kernel-harness.md`
**Owning repo**: `tantra-examples` (depends on the Thrust A wheel surfaces from
`tantra-ffi/docs/plans/0002-*.md`, rows T13.1–T13.5)

## Symptom

After Thrust A lifts the domain/math modules into the wheel, `tantra_examples/_kernel/`
still holds eight application-harness modules under a name ("`_kernel`") that implies
kernel/domain internals — a leftover of the (now fully dismantled) kernel mirror. The
examples package is the learning path (AGENTS §2.1); its own scaffolding should be named for
what it is, not for a kernel that no longer exists in the repo.

## What moves (harness rename, `_kernel` → `tantra_examples/harness/`)

| Module | Public API | Retarget notes |
| :--- | :--- | :--- |
| `config.py` | `StrategyConfig` | `_kernel/loader.py`, `tests/integration/test_06_equal_weight_rebalance_parity.py` |
| `loader.py` | `find_catalog`, `load_catalog_strategy`, `CatalogError` | `tantra_examples/catalog.py`, examples `screening/06`, `universes/07`, tests/integration |
| `log.py` | `register_event`, `setup_event_logging` | `_kernel/runner.py` (moves with it) |
| `manifest.py` | pipeline manifest handling | tests/unit |
| `ports.py` | `BarStore`, `MarketDataProvider`, `validate_bar` | `_kernel/service.py`, `examples/storage/01` |
| `runner.py` | `StrategyRunner` | `tantra_examples/backtest.py` |
| `service.py` | `DataService` | `sip_plan.py` |
| `testing.py` | `replay`, `ReplayResult` | ~20 examples + tests |

Plus: rewrite the facade `__init__.py` — after Thrust A it must stop re-exporting wheel
domain names (`Bar`, `Money`, `Position`, … — those come from the wheel) and only expose the
harness's own public names.

## How to close

1. **Move** the 8 modules into `tantra_examples/harness/`; rewrite the intra-`_kernel`
   imports (`from tantra_examples._kernel.ports import …` → `from tantra_examples.harness.ports import …`).
2. **Retarget every `tantra_examples._kernel.*` import** (~60 sites across
   `tantra_examples/`, `examples/`, `tests/`): domain imports → wheel `tantra.*` (Thrust A),
   harness imports → `tantra_examples.harness.*`.
3. **Delete `tantra_examples/_kernel/`** — the package name disappears from the repo.
4. **Docs sweep** — `docs/design/architecture.md`, `code-migration-map.md`,
   `gap-cascade-kernel-mirror.md` (any remaining `_kernel` mirror/harness lists), READMEs
   that name `_kernel` modules, `.agents/HANDOFF.md`.
5. **Gate** — `/project1/vyapaar-labs/tantra-ffi/.venv/bin/pytest tests/unit -q` (baseline
   841 passed / 73 pre-existing float-rooted failures / 3 environmental errors / 50 skipped —
   zero new failures), `ruff check .` + `ruff format --check .` clean, and smoke-run a
   representative set of examples (`basic/01`, `options/02`, `backtesting/01`,
   `screening/06`, `universes/07`, `ai_research/03`).

## Phase C — gate + follow-on consolidation candidates (T13.7)

Recorded candidates for later absorption into wheel / `tantra_data` services (kept
documented, NOT required to close this plan):

- `harness/runner.py` (`StrategyRunner`) vs the wheel `tantra.backtest.session.Tantra.backtest`
  — assess whether `tantra_examples/backtest.py`'s `run_portfolio_backtest` can run on the
  wheel session.
- `harness/service.py` (`DataService`) vs `tantra_data`'s service layer.
- `harness/testing.py` (`replay`) as a future wheel backtest-replay helper.

## Dependency

Executes after Thrust A (T13.1–T13.5): the retarget of the domain imports targets the wheel
surfaces, which must exist first. The harness rename itself is otherwise independent.

## Non-goals

- No new domain logic; no Rust/PyO3 changes; no wheel changes (this repo).
- The harness modules are not deleted — they are the examples' legitimate application-layer
  scaffolding, only renamed and re-homed.
