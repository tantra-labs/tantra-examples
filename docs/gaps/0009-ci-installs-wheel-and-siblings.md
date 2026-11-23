# 0009 — CI installs neither the wheel nor the sibling packages it tests against

**Status**: open
**Filed**: 2026-11-23 — workspace design review (root plan 0021) · **Kind**: deployment · **Severity**: high
**Plan**: [0006](../plans/0006-design-review-2026-11.md)

## What's stubbed or hardcoded

The CI workflow gates a suite it cannot import.

- `.github/workflows/ci.yml:21` installs only `ruff mypy pytest polars pydantic`.
- `pyproject.toml:13-16` hard-depends on `tantra>=0.1.0`, `tantra-adapters`, `tantra-data`, `tantra-strategies`.
- `tests/unit/conftest.py:10` imports `duckdb`, which exists only in the `screening` extra (`pyproject.toml:44`).
- `tests/unit/conftest.py:13` imports `tantra_examples.provision.dummy`.
- `tantra_examples/harness/service.py:14-20` imports `tantra.bar`, `tantra.coverage`, `tantra.instrument`, which ship only in the wheel.
- `mypy tantra_examples` (`ci.yml:25`) cannot resolve `tantra.*`.
- Package version is `0.1.0` with floor-only dependency pins (`tantra>=0.1.0`); a wheel API change breaks installs with no upper bound.

## Why

A pull-request run either fails at import (permanently red, then ignored) or, if wheel stubs are cached elsewhere, nothing proves the 909 unit tests pass. The gate is not real, so an API rename in the wheel can land unnoticed. This is the examples-repo face of root gap 0024 (no CI for the Rust repos) and root plan 0023.

## How to close it

1. Build the `tantra` wheel with maturin in CI (or install the workspace build artifact) and install it before the test job.
2. Install `pip install -e ".[dev,ai,screening]"` plus the sibling packages `tantra-adapters`, `tantra-data`, `tantra-strategies`.
3. Add `duckdb` to the dev/test extras; add `fastapi` and `uvicorn` via the `provision` extra from [0011](0011-provision-server-deps-and-openapi-copy.md).
4. Pin compatible version ranges (upper bounds) for the wheel and siblings in `pyproject.toml`.
5. Cache the wheel keyed on its hash so PR runs stay fast.
6. Run `ruff check .`, `ruff format --check .`, `mypy tantra_examples`, `pytest -q tests/unit` as separate steps.

**Verification**: CI run on a clean runner passes with all 909 unit tests collected; deliberately removing the wheel install step turns the job red at import; `mypy tantra_examples` resolves `tantra.*`.

## Related

- Root gap 0024 (no CI for Rust repos), root plan 0023 (build/CI/release engineering), root gap 0025 (non-reproducible builds, no Python lockfiles).
- [0011](0011-provision-server-deps-and-openapi-copy.md) — undeclared `provision` dependencies the CI install must cover.
- Plan 0006 R1 — smoke-run of `examples/` scripts builds on this install.
