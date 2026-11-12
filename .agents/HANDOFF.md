# `tantra-examples` — Inter-Agent Handoff

## Phase / Slice Status
* **Honba staged port (plan 0002)** — **ALL 9 STAGES COMPLETE (Stages 0–8)**; recorded Implemented in `docs/plans/README.md` (commit `bbfa692`). Plan doc cleaned up per gap-tracking §4.
* **Docs (this change)**: former `docs/roadmap/` (`roadmap.md` + `migration-verification.md`) dismantled into `docs/design/` (`architecture.md`, `implementation-record.md`, `code-migration-map.md`), `docs/gaps/` (README + 0001–0008 source-verified), and `docs/plans/README.md`; `docs/reference/` concept docs unchanged.
* Full verification gates were green at port close: `pytest -q` (922 passed, 70 skipped), `ruff check .`, `ruff format --check .`, `mypy tantra_examples` (234 files), `make check`.

## Decisions & Discoveries
* **Pytest import mode & test structure**: `pythonpath = ["."]` in `pyproject.toml` + empty `__init__.py` in `tests/`, `tests/unit/`, `tests/integration/` lets `pytest -q` run from the repo root and resolves module-name collisions between unit and integration tests.
* **Kernel mirror is the wheel-missing stand-in**: `tantra_examples/_kernel/` is a 166-file kernel-verbatim mirror (indicators 87, portfolio_strategy 10, adapters 13) cited against gaps 0002–0008. `native.py` pins `SCHEMA_VERSION=8`, `API_VERSION="v1"`, `STRATEGY_API_VERSION="1.0.0"`. `pyproject.toml` `[[tool.mypy.overrides]]` disables `override` for `_kernel.indicators.*`, `_kernel.declarative`, `_kernel.portfolio_strategy.*`.
* **Gap 0004 stream plumbing**: the standalone screener CLIs stream through `screener_cli.py` + `pipeline/io.py` (`read_symbols`/`to_stream`/`parse_symbols`/`dumps`), not a `stream.py` module.
* **Gap 0005**: only `examples/options/07_large_qty_options_slicer.py` probes optional `tantra_te_slicer`; `examples/stocksharp/02_twap_vwap.py` imports `tantra_examples.options` directly.
* **Pitfalls contract**: flat foundational scripts (15) have 2–3 bullets; topic scripts (94) have 3–6. `test_pitfalls_sections.py` accommodates both.
* **Offline catalog seam**: integration tests that require the multi-GB real Parquet catalog skip when run offline (`VYAAPAAR_DATA_DIR` synthetic fixture seam, gap 0003).

## Immediate Next Step
* All 9 stages of the `honba-examples` port are complete and verified; docs batch committed.
* Next open work is gap-driven (all 0001–0008 owned by other repos): close a gap when its owning surface ships, then delete the mirror/stub and retarget consumers.

## Operating Invariants
* Zero floats in financial math (documented exceptions: BS internals example 13; grafted `metrics.py` stats; kernel-mirror float domain, gap 0006). Deterministic offline runs; tests live in `tests/` only.
* Canonical verification: `pytest -q && ruff check . && ruff format --check . && mypy tantra_examples && make check`.
