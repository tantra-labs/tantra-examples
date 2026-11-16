# Plans Index — `tantra-examples`

Per workspace rule `.agents/rules/gap-tracking.md`:
- Gaps are individual features (`docs/gaps/XXXX-*.md`).
- Plans are collections of gaps (`docs/plans/XXXX-*.md`).
- When implemented, plan documents are cleaned up from `docs/plans/` and recorded in this index.

## Active Plans

| # | Title | Target Scope | Status |
|---|-------|--------------|--------|
| — | (none) | — | — |

## Implemented Plans

| # | Title | Target Scope | Implemented In |
|---|-------|--------------|----------------|
| 0001 | Example Notebooks for Fincept-Gap-Closing Features | `examples/` | Implemented in commit `552c873` (examples 12–15: portfolio allocation, Black-Scholes Greeks, timeseries forecast, Fama-MacBeth) |
| 0002 | Staged Port: `honba-examples` → `tantra-examples` | `examples/`, `tantra_examples/`, `tests/` | Implemented in commit `bbfa692` (all 9 stages 0–8 complete; 94 topic scripts, 130 test files) |
| [0003](0003-tantra-examples-harness-dismantle.md) | Dismantle `_kernel` — harness rename to `tantra_examples/harness/`, retarget all `_kernel.*` import sites, delete `_kernel/`, gate + follow-on candidates (T13.6–T13.7) | `tantra_examples/`, `examples/`, `tests/`, docs | 2026-11-16: `1acabfb9` (Thrust B rename + delete), `3c2e5ae` (HANDOFF/plan-commit hash); gate verified — `tests/unit` 909 passed / 51 skipped, zero new failures (6 pre-existing `test_06_multi_broker_dispatch` env failures — installed `tantra_adapters` entry points bypass the example's paper fallback), ruff clean, smoke imports 6/6 |
| [0004](0004-data-provisioning-microservice-scope.md) | Data-Provisioning Microservice (download / dummy / Monte-Carlo) — **T15.1–T15.6 shipped 2026-11-16**: `tantra_examples/provision/` (layout + contracts + dummy + monte-carlo + download + server + client + openapi.json + seam), one canonical synthetic source, HTTP microservice with background jobs + cancel, example runtime seam; per-test writers folded; **follow-on same day** — seam wired into `ScreenerCLIExample` (interactive prompt when the catalog is absent), `--data-dir` accepts a data root or catalog dir, missing-catalog message fixed, data-root env var renamed `TANTRA_DATA_DIR` | new service component; `tantra_examples/provision/`, `tests/` | 2026-11-16: `f76428b` (M1), `5cd3897` (M2+M3), `7b98b78` (M4+M5), `36e468f` (M6), seam wiring follow-on; gate — `tests/unit` 1018 passed / 1 skipped (skip = mutual_funds store, tantra-data gap 0023), ruff clean, mypy clean on `provision/` |

## Cleanup note

The former `docs/roadmap/` (`roadmap.md` + `migration-verification.md`) was dismantled
into `docs/design/` (`architecture.md`, `implementation-record.md`, `code-migration-map.md`),
`docs/gaps/` (open mirror/stub items 0001–0008), and this index. Completed milestones are
recorded in [`docs/design/implementation-record.md`](../design/implementation-record.md);
no further roadmap documents exist.
