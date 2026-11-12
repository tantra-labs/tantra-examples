# `tantra-examples` — Migration Map (honba-examples → tantra-examples)

> **Tier**: Tier 6D
> **Source**: `honba-workspace/honba-examples`
> **Target**: `tantra-examples`
> **Status**: Migration complete (staged port, all 9 stages 0–8). The milestone record
> lives in [`implementation-record.md`](implementation-record.md); this file is the
> historical layout mapping.

## Layout mapping

The port did **not** copy the `honba-examples` source wholesale: the fresh entry
journey (`examples/01`–`15`) and the fresh `backtest.py`/`metrics.py`/`data.py` Decimal
world stay canonical, and the source's topic capabilities were grafted in per the
staged port's overlap policy (D3). What came from where:

| Source capability | Ported to | Notes |
|---|---|---|
| Entry journey (flat `01`–`15`, 8-module harness) | `examples/` + fresh `tantra_examples/` harness | Written fresh; canonical |
| Topic scripts (`basic`, `candles`, `strategies`, `backtesting`, `optimizer`, `storage`, `universes`, `mutual_funds`, `screening`, `options`, `stocksharp`, `ai_research`, `production`) | `examples/<topic>/NN_*.py` (94 scripts) | Grafted per D3 overlap policy |
| Shared harness backtest / metrics / pipeline / screening / ewr / options / optimizer / ai_replay | `tantra_examples/` subpackages + modules | Grafted; fresh `backtest.py`/`metrics.py` remain canonical |
| Kernel domain modules (tamashii `strategies/`, `domain/`, `screener/`) | `tantra_examples/_kernel/` (166 files) | Kernel-verbatim mirror (gap 0006/0007) |
| Adapter framework (`honba.adapters`) | `tantra_examples/_kernel/adapters/` (13 files) | Mirror (gap 0007); `rest.py`/`gateway.py` excluded pending the client surface |
| `honba.algo_analytics` engine | `tantra_examples/optimizer/algo_analytics/` | Engine mirror (gap 0001) |
| `honba.ai.*` LLM/decision surface | `tantra_examples/_kernel/ai/`, `fake_llm.py`, `decision_guard.py` | Mirror/scripted paths (gap 0002) |
| Loader / store / mutual-funds / coverage (`tantra_data`) | `amfi.py`, `bhavcopy.py`, `screening/paths.py` seam | In-repo stand-ins (gap 0003) |
| Display / universes / client (`honba.display`, `honba.markets.india.universes`, `honba.client`, `honba.cli.data`) | `display_style.py`, `universe_lists.py`, `cli.py`, `screener_cli.py`, `options/*` | Mirrors (gap 0004) |

## Executed Verification Pipeline

```bash
# Run from the repository root
pytest -q
ruff check .
ruff format --check .
mypy tantra_examples
```

All verification gates pass cleanly without external network or broker dependencies:
- `pytest -q`: 922 passed, 70 skipped, 0 failures
- `ruff check .`: clean
- `ruff format --check .`: clean
- `mypy tantra_examples` (234 files): clean
- `make check`: green

## Open dependency surface

The in-repo mirrors listed above are all open gaps owned by other repos. Each gap doc
in [`docs/gaps/`](../gaps/README.md) names the owning surface and the exact files to
delete when it ships — see the individual gap files for the closing procedure.
