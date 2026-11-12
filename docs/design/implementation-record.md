# `tantra-examples` — Implementation Record

Dismantled from the former `docs/roadmap/` (`roadmap.md` +
`migration-verification.md`). Completed milestones are recorded here; remaining
future work moved to [`docs/gaps/`](../gaps/README.md) and
[`docs/plans/`](../plans/README.md).

## Migration: `honba-examples` → `tantra-examples` (Tier 6D)

| Milestone | Status | Commit |
|-----------|--------|--------|
| `pyproject.toml` fixed (invalid `rust_decimal` dependency removed) | Complete | staged port Stage 0 |
| Entry journey implemented fresh (flat `examples/01`–`15`, 8-module harness, per-example regression tests) | Complete | staged port Stage 1 |
| Staged port Stages 0–8: pre-flight → shared harness → basic/candles/strategies → backtesting/optimizer → storage/universes/mutual-funds → screening → options/stocksharp → ai_research/production → docs & sweep | Complete | `bbfa692` (all 9 stages) |
| Full verification suite: 130 test files (124 unit, 5 integration, 1 root test_init) + 2 snapshot goldens, `Pitfalls::` docstring contract test | Complete | Stage 8 |
| Zero `honba` identifiers across `examples/`, `tantra_examples/`, `tests/` | Complete | sweep (Stage 8) |
| Platform rename `vyapaar-*` → `tantra-*` | Complete | `792e4b8` |
| Docs: roadmap dismantled into `docs/design/` + `docs/gaps/` + `docs/plans/` | Complete | this change |

The file-by-file mapping is in [`code-migration-map.md`](code-migration-map.md).

## Subsequent landings

| Landing | Commit |
|---------|--------|
| Plan 0001 — Example notebooks for Fincept-gap-closing features (`examples/12`–`15`: portfolio allocation, Black-Scholes Greeks, timeseries forecast, Fama-MacBeth) + `tantra_examples/quant.py` | `552c873` |
| Plan 0002 — Staged port `honba-examples` → `tantra-examples` (all 9 stages, 94 topic scripts, 130 test files) | `bbfa692` |
| Docs: `docs/roadmap/` dismantled into `docs/design/` / `docs/gaps/` / `docs/plans/` | this change |

## Verification (recorded gate, staged port)

```bash
pytest -q               # 922 passed, 70 skipped, 0 failures
ruff check .            # clean
ruff format --check .   # clean
mypy tantra_examples    # clean (234 files)
make check              # green
```

- Zero inline `test_*` functions in `tantra_examples/` (tests live in `tests/` only).
- Zero `honba` identifiers anywhere in the ported code.
- `tests/unit/test_pitfalls_sections.py` enforces the `Pitfalls::` docstring contract
  over all 94 topic scripts and 15 flat scripts.

## Open future work

All open items now live in [`docs/gaps/`](../gaps/README.md) — currently eight
source-verified gaps (0001–0008) covering the wheel/owner surfaces that the in-repo
mirrors stand in for: algo-analytics engine (0001), AI provider/agent loop (0002),
`tantra-data` loaders (0003), display/universe/client + India market-pack (0004),
`tantra-exec` freeze slicer (0005), the kernel-domain surface (0006), the adapters
framework (0007), and the runtime session orchestrator (0008).
