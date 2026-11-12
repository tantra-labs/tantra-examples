# 0003 — tantra-data-nav-loaders

**Status**: open
**Owning repo**: `tantra-data` (Python + DuckDB lakehouse: loaders, store, coverage
ledger).

## Symptom
`tantra_data` has no installed surface yet: `vx.loaders.{nse, yfinance}`,
`vx.loaders.amfi` NAV ingestion, `store.coverage`, and the lakehouse paths the
screener/sip harness resolve are absent, so the ported consumers keep in-repo shims.

## What stands in
* `tantra_examples/amfi.py` — AMFI NAV loader: `parse_navall` / `nav_bars` / `NavRow` /
  `NavSkip`, producing daily kernel `Bar`s stamped at the 09:15 IST session open. The NAV
  loading capability whose store surface (`store.mutual_funds`) the wheel data repo will
  provide.
* `tantra_examples/bhavcopy.py` — NSE bhavcopy dialect-sniffing CSV parser
  (UDiFF / Sec-Bhavdata / legacy), used by `examples/storage/02_import_nse_bhavcopy.py`.
* `tantra_examples/screening/paths.py` — `VYAAPAAR_DATA_DIR` env seam prepended to the
  catalog / `fundamentals.duckdb` / `mutual_funds.duckdb` discovery lists; the
  `tests/unit/conftest.py` `catalog_dir` / `add_series` / `fund_db` synthetic fixtures
  power it offline when no `tantra-data` checkout exists beside the repo.
* `tantra_examples/_kernel/data/__init__.py` — `Quantity` / `parse_quantity` mirror
  (`# mirror: kernel-verbatim port (gap 0003: tantra-data quantity query)`).
* `tantra_examples/_kernel/screener/` — catalog + coverage mirrors
  (`# mirror: kernel-verbatim port (gap 0003: screener coverage surface)`).
* `tantra_examples/sip_plan.py` — best-effort `tantra_data.loaders.{nse,yfinance}`
  try-import for gap downloads, falling back to the in-repo store.

## How to close
Land `tantra-data` with the loaders/store/coverage surface (point-in-time NSE parquet
catalog, `fundamentals.duckdb`, `mutual_funds.duckdb`, NAV ingestion). Then delete
`amfi.py`'s loader duplication, `bhavcopy.py`, `_kernel/data/`, `_kernel/screener/`, and
the env/test seam; retarget the `tantra_data.*` imports and drop the conftest synthetic
catalog fixtures where the real surface covers CI.
