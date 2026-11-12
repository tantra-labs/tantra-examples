# 0004 — tantra-wheel-display-universes-client

**Status**: open
**Owning repo**: `tantra-ffi` (wheel: `tantra.display`, `tantra.client`,
`tantra.markets.india.universes`, `tantra.cli.data`).

## Symptom
The wheel offers no display, universe, or client surface for the console output the
examples use.

## What stands in
* `tantra_examples/display_style.py` — console/table formatting mirror (Indian money
  grouping, table renderer), including the `format_money` graceful try-import of the
  future `tantra.utils.format` surface (comment cites this gap).
* `tantra_examples/universe_lists.py` — NIFTY50 / BANKNIFTY / Alpha30 universe mirrors
  (`resolve_universe`, constituents, `save_universe_history`).
* `tantra_examples/screener_cli.py` + `tantra_examples/stream.py` — output/stream
  plumbing the standalone CLIs print through.
* `tantra_examples/cli.py` — the base example CLI (out/format/width flags) replacing
  `honba.cli.data`.
* `tantra_examples/options/*` — instrument lookups via a best-effort
  `tantra.client.get_instrument` try-import (comment cites this gap).

## How to close
Ship the wheel display/universe/client modules; delete the mirrors and retarget the D5
imports (`from tantra.display → ...`, `from tantra.markets.india.universes → ...`).
