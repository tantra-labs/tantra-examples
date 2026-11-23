# 0006 — tantra-examples design review (2026-11): runnable CI, wheel-backed harness & Decimal-correct teaching

**Status**: Proposed (2026-11-23)
**Scope**: `tantra-examples` · **Umbrella**: root `docs/plans/0021-workspace-design-review-2026-11.md`

## 0. Executive Summary & Objective

The examples repo is the learning path users copy from, but its CI cannot import what it tests, its metrics and backtest records use floats while claiming exact Decimal, the `provision` service imports undeclared packages, and several harness modules still mirror code now owned by `tantra-strategies` and the wheel. This plan makes the CI gate real, removes float math from teaching code, and retires the remaining mirrors.

Non-goals: dismantling duplicated Rust/Python quant math (root gap 0015), the unified simulation model (root gap 0021) and the generic CI build (root plan 0023) are owned elsewhere; this plan only consumes them. Plan 0005 (categorised examples) is unaffected except where noted in R1 and R4.

## 1. Context & Gaps Covered

| Gap | Title | Kind | Severity |
|---|---|---|---|
| [0009](../gaps/0009-ci-installs-wheel-and-siblings.md) | CI installs neither the wheel nor the sibling packages | deployment | high |
| [0010](../gaps/0010-metrics-float-and-wheel-duplication.md) | `metrics.py` float metrics duplicate the wheel | duplication | medium |
| [0011](../gaps/0011-provision-server-deps-and-openapi-copy.md) | `provision` server undeclared deps and OpenAPI copy | design-flaw | medium |
| [0012](../gaps/0012-backtest-float-fills.md) | `backtest.py` float fills and two engines | design-flaw | medium |

Plan-only items (no standalone gap doc):

- **R1 — Smoke-run of `examples/` scripts**: `tests/conftest.py:5,29-31` only imports example modules via `importlib.util.spec_from_file_location`; only `tests/integration/test_pipeline_chaining.py` and `tests/integration/test_07_alpha30_backtest.py` execute scripts; about 45 others never run.
- **R2 — Harness mirrors the manifest and runner owned elsewhere**: `tantra_examples/harness/manifest.py:1,250` (432 lines, `class StrategyManifest(_Strict)`) duplicates `tantra-strategies/tantra_strategies/manifest/strategy.py:84`; `harness/runner.py:1` (653 lines) mirrors the Rust `StrategyRunner` exposed in `tantra-ffi/crates/tantra-ffi-py/src/runner.rs`; `harness/config.py:4` and `harness/loader.py:14` are verbatim kernel mirrors.
- **R3 — Residual `honba` identifiers and graft provenance**: `tantra_examples/backtest.py:213`, `tantra_examples/settlement.py:32`, `tantra_examples/harness/testing.py:7`, `harness/config.py:4`, `harness/loader.py:14`, `harness/manifest.py:1`, `pyproject.toml:35`; `tests/unit/test_06_mcp_integration.py:27` pins `"honba-codegen"`.
- **R4 — Silent synthetic data in the loading-data path**: `examples/01_loading_data.py:3,21,49` loads `synthetic_bars(instrument, days=250, seed=42)` and prints coverage as market data; 46 files under `examples/` reference `synthetic`/`TANTRA_DATA_DIR`; the mutual-fund loader stub `AmfiNavLoader.load_category` returns `{}` (noted in `tantra-docs/docs/examples/known_issues.md`).

## 2. Component Specifications & Phases

### Phase A — Make the gate real and fix honesty issues
1. **0009**: wheel + sibling install, extras, version ranges, wheel-hash cache in `.github/workflows/ci.yml`.
2. **0011** (steps 1 and 3): declare the `provision` extra; generate `openapi.json` in a test instead of committing it.
3. **R3**: rewrite comments to real `tantra-*` paths; make the MCP test assert a stable field rather than the `honba-codegen` substring, and raise the legacy string upstream with the owning repo.
4. **R4**: add a one-line banner `DATA SOURCE: synthetic (seed=42)` in `tantra_examples/output.py` whenever a synthetic path is used; make stubs such as `AmfiNavLoader.load_category` raise an explicit "unavailable" error instead of returning `{}` (cite root gap 0012).

**Gate**: `ruff check .`, `ruff format --check .`, `mypy tantra_examples`, `pytest -q tests/unit`.

### Phase B — Remove floats and mirrors
1. **0010**: delete float metrics helpers, call wheel functions, Decimal P&L in optimizer examples, hypothesis parity test.
2. **0012**: Decimal fill/order records, regenerate `tests/snapshots/`, parity test, fold or delete the grafted engine.
3. **R2**: retarget examples to `tantra_strategies.manifest`; replace `harness/runner.py` with the wheel `StrategyRunner`; keep only `ports.py` and `testing.py` doubles; contract test loading one manifest through both parsers until the mirror is deleted.
4. **0011** (step 2): decide whether the provisioning service moves to `tantra-data` or is labelled example-only.

**Gate**: as Phase A plus `pytest -q tests/snapshots` and the parity tests.

### Phase C — Continuous verification of the learning path
1. **R1**: add `tests/smoke/test_examples_run.py` parametrised over `examples/**/*.py`, offline, with `TANTRA_DATA_DIR` pointed at the synthetic lakehouse (`tests/unit/synthetic_lakehouse.py`) and a per-script timeout; allow-list known-template scripts (`production/02_*`, `05_*`); also assert the R4 banner; run as a separate CI job.
2. Fix or remove `production/05_deployment.py`, which generates systemd/Dockerfile units pointing at a non-existent `tantra.session.run` module (`tantra-docs/docs/examples/known_issues.md`).

**Gate**: `pytest -q tests/smoke` green in CI on a clean runner.

## 3. Relationship to Other Plans

- Root plan 0019 (audit): not duplicated; the wheel-runner and metrics moves align with its P2 items.
- Root plan 0023 (build/CI/release) and root gap 0024 supply the shared wheel build that 0009 consumes; root gap 0025 covers Python lockfiles.
- Root gaps 0015 (quant math), 0021 (simulation), 0022 (OpenAPI), 0012 (fabricated data) are the cross-repo owners of the corresponding items here.
- Plan 0005 (categorised examples) gains the R1 smoke job and R4 banner for its new scripts; no scope change.
- Provider repos: `tantra-ffi` (wheel analytics/backtest/runner), `tantra-strategies` (manifest), `tantra-data` (provisioning service).

## 4. Exit Criteria

1. CI on a clean runner installs the wheel and siblings and runs all `tests/unit` plus mypy without import errors.
2. No `float` in public fill/order records or metrics helpers; Decimal parity tests pass.
3. `import tantra_examples.provision.server` works after installing the `provision` extra; no committed `openapi.json` without a drift test.
4. No `honba` identifiers remain outside historical migration docs.
5. Every example script is smoke-run (or explicitly allow-listed) and prints a data-source banner when synthetic.
6. `harness/manifest.py`, `harness/runner.py`, `harness/config.py` and `harness/loader.py` mirrors are removed or reduced to test doubles.
