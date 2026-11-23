# 0011 — `provision` HTTP server imports undeclared dependencies and commits a third OpenAPI copy

**Status**: open
**Filed**: 2026-11-23 — workspace design review (root plan 0021) · **Kind**: design-flaw · **Severity**: medium
**Plan**: [0006](../plans/0006-design-review-2026-11.md)

## What's stubbed or hardcoded

- `tantra_examples/provision/server.py:12-14` imports `fastapi`, `uvicorn` and `fastapi.responses`.
- `pyproject.toml:12-18,25-47` declares neither package, in the base dependencies or in any extra; `tests/unit/conftest.py` also pulls `duckdb` outside the base dependencies (see [0009](0009-ci-installs-wheel-and-siblings.md)).
- `tantra_examples/provision/openapi.json` is a hand-committed OpenAPI file, a third copy next to `tantra-ffi/schema/openapi.json` and `tantra-market/schema/openapi/openapi.json`.
- The service overlaps `tantra-data`: `tantra_examples/harness/service.py:65` `DataService` versus `tantra-data/tantra_data/ports/repositories.py:410` `DataService` Protocol.
- `provision/server.py` is a long-running service with an in-process thread pool and no health or shutdown story, yet is documented as a microservice.

## Why

`pip install tantra-examples` followed by importing `provision` raises `ImportError`. A committed `openapi.json` drifts silently from the FastAPI app and adds a third unowned schema copy to a workspace that is trying to reach one canonical document (root gap 0022). Ownership of a data-provisioning service is ambiguous between examples and `tantra-data`.

## How to close it

1. Declare a `provision` extra (`fastapi`, `uvicorn`) in `pyproject.toml` and include it in the CI install.
2. Decide ownership: move the service to `tantra-data` (file the gap there) or mark it explicitly as example-only, non-production code in its docstring and docs.
3. Generate `openapi.json` from the app inside a test and compare, rather than hand-committing it; drop the committed copy once the canonical document and generated clients exist (root gap 0022).
4. If kept, add a trivial health route and graceful shutdown, or document their absence.

**Verification**: fresh-venv `pip install -e ".[provision]"` then `python -c "import tantra_examples.provision.server"` succeeds; a test fails when the app schema differs from the checked artifact (or the artifact is removed); `pytest -q tests/unit`.

## Related

- Root gap 0022 (one canonical OpenAPI document and generated clients).
- Root plan 0006 follow-on "service -> tantra_data" (partial overlap); `tantra-data` plan for provisioning ownership.
- [0009](0009-ci-installs-wheel-and-siblings.md) — CI must install the new extra.
