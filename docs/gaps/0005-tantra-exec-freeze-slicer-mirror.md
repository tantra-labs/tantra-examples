# 0005 — tantra-exec-freeze-slicer-mirror

**Status**: open
**Owning repo**: `tantra-exec` (freeze slicer crate) / `tantra-ffi` (wheel
`Sizer` surface).

## Symptom
There is no real `tantra-exec` freeze-limit auto-slicer package, and the
wheel's `Sizer` type cannot slice an order against a freeze limit.

## What stands in
`tantra_examples/options/__init__.py`'s `freeze_limit_qty()` / `slice_order()`
/ `verify_slices()` (plus `option_sell_stt`, `fno_turnover`, `GreekRiskBounds`)
stand in for the real crate.

* `examples/options/07_large_qty_options_slicer.py` probes for an optional
  `tantra_te_slicer` package (`_te_slicer_available` / `_slice_with_te_slicer`) and
  falls back to the same local mirror when it's absent (which it always is today);
  the script carries a `# stand-in for docs/gaps/0005-...md` citation.
* `examples/stocksharp/02_twap_vwap.py` imports the local mirror directly
  (`from tantra_examples.options import freeze_limit_qty, verify_slices` and
  `slice_order as _ref_slice_order`) to check every child slice against the limit.

## How to close
Once `tantra-exec`/`tantra-ffi` ship a real slicer surface, delete the local
mirror in `tantra_examples/options/__init__.py` and retarget both scripts'
imports to the real package.
