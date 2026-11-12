# 0004 — tantra-wheel-display-universes-client

**Status**: open
**Owning repo**: `tantra-ffi` (wheel: `tantra.display`, `tantra.client`,
`tantra.markets.india.universes`, `tantra.cli.data`) and `tantra-market` (India market
pack: costs + settlement schedules).

## Symptom
The wheel offers no display, universe, client, or India market-pack surface for the
console output and cost/settlement math the examples use.

## What stands in
* `tantra_examples/display_style.py` — console/table formatting mirror (Indian money
  grouping, table renderer), including the `format_money` graceful try-import of the
  future `tantra.utils.format` surface (comment cites this gap).
* `tantra_examples/output.py` — one print-through point for every example
  (`add_output_args`, `resolve_output`, `print_metrics`/`print_run_header`/…).
* `tantra_examples/universe_lists.py` — NIFTY50 / BANKNIFTY / Alpha30 universe mirrors
  (`resolve_universe`, constituents, `save_universe_history`).
* `tantra_examples/screener_cli.py` + `tantra_examples/pipeline/io.py` — the
  stream-friendly screener CLI base and the symbol/JSON stream helpers
  (`read_symbols`, `to_stream`, `parse_symbols`, `dumps`) the standalone CLIs print
  through.
* `tantra_examples/cli.py` — the base example CLI (parser / `--out` / JSON emit)
  replacing `honba.cli.data`.
* `tantra_examples/options/*` — instrument lookups via a best-effort
  `tantra.client.get_instrument` try-import (comment cites this gap).
* `tantra_examples/_kernel/markets/india/` — `costs.py` + `settlement.py` kernel-verbatim
  mirrors of the India market pack (NSE/BSE equity delivery costs; T+2-before-2023-01-27
  / T+1-from-then settlement). Cited `# mirror: kernel-verbatim port (gap 0004)`.
* `tantra_examples/_kernel/cli/__init__.py` — global-store accessor mirror
  (`# mirror: kernel-verbatim port (gap 0004: wheel display/client surface)`).
* `tantra_examples/_kernel/backtest/simulated.py` — uses the mirrored India
  costs/settlement via `settlement_days_for` (gap 0004 comment).

## How to close
Ship the wheel display/universe/client modules and the India market-pack surface; delete
the mirrors and retarget the imports (`from tantra.display → ...`,
`from tantra.markets.india.universes → ...`, `from tantra.markets.india.costs → ...`).
