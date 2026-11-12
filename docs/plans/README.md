# Plans Index — `tantra-examples`

Per workspace rule `.agents/rules/gap-tracking.md`:
- Gaps are individual features (`docs/gaps/XXXX-*.md`).
- Plans are collections of gaps (`docs/plans/XXXX-*.md`).
- When implemented, plan documents are cleaned up from `docs/plans/` and recorded in this index.

## Active Plans

| # | Title | Target Scope | Status |
|---|-------|--------------|--------|

## Implemented Plans

| # | Title | Target Scope | Implemented In |
|---|-------|--------------|----------------|
| 0001 | Example Notebooks for Fincept-Gap-Closing Features | `examples/` | Implemented in commit `552c873` (examples 12–15: portfolio allocation, Black-Scholes Greeks, timeseries forecast, Fama-MacBeth) |
| 0002 | Staged Port: `honba-examples` → `tantra-examples` | `examples/`, `tantra_examples/`, `tests/` | Implemented in commit `bbfa692` (all 9 stages 0–8 complete; 94 topic scripts, 130 test files) |

## Cleanup note

The former `docs/roadmap/` (`roadmap.md` + `migration-verification.md`) was dismantled
into `docs/design/` (`architecture.md`, `implementation-record.md`, `code-migration-map.md`),
`docs/gaps/` (open mirror/stub items 0001–0008), and this index. Completed milestones are
recorded in [`docs/design/implementation-record.md`](../design/implementation-record.md);
no further roadmap documents exist.
