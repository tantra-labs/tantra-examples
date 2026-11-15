# 10 Production – paper trading, live, monitoring, deployment

Production examples demonstrate the path from backtest to live trading. The first
three wire up an inline SMA-crossover strategy (`SmaPaper`, `SmaLive`, `SmaMulti`)
selected with `--strategy sma_crossover`; the last two are operational tooling with
no strategy. All examples run offline and deterministically on the `fake` adapter
unless you explicitly opt into a real broker (`--no-dry-run` on the Dhan example).

## At a glance

| #  | File                          | Strategy / focus  | What you learn                                                         |
|----|-------------------------------|-------------------|------------------------------------------------------------------------|
| 01 | `01_paper_trading.py`         | SMA crossover     | Paper trading session: simulated fills, per-bar mark-to-market equity  |
| 02 | `02_live_trading_dhan.py`     | SMA crossover     | Dhan template: dry-run echo; live session code is commented out        |
| 03 | `03_multi_account.py`         | SMA crossover     | Multiple accounts: isolate capital, aggregate P&L, per-account risk    |
| 04 | `04_monitoring.py`            | —                 | Metrics/health endpoint shape (values are simulated)                   |
| 05 | `05_deployment.py`            | —                 | Systemd/container deploy: config, secrets, logging, graceful shutdown  |
| 06 | `06_multi_broker_dispatch.py` | SMA crossover     | Same strategy dispatched across Zerodha, Angel One (paper mode) and Upstox (scaffold); asserts adapter-agnostic parity |

## Pitfalls checklist

Every numbered script in this directory has a `Pitfalls::` section in its module docstring (enforced
by `tests/unit/test_pitfalls_sections.py`): the traps specific to what that script does, such as
paper fills that are not live fills, risk-limit arguments that are echoed but not enforced, live
scripts that are templates, secrets on the command line, duplicate order submission and restart
reconciliation, IST market hours, simulated metrics that cannot alert, and config and image drift in
the generated deployment files. Read it before trusting a number. For the general treatment see
[Avoiding backtest biases](https://tantra-labs.github.io/tantra/book/backtesting/avoiding_backtest_biases.html).

## The production pattern

```python
from tantra.adapters.registry import AdapterRegistry
from tantra.backtest.session import Tantra

# 1. Resolve a broker adapter (fake by default; the wheel ships no live
#    REST client yet — tantra.client is a future surface)
registry = AdapterRegistry()
dhan = registry.create("dhan", **{"client_id": "...", "access_token": "..."})

# 2. Backtest the strategy offline through the wheel session (next-open
#    fills, NSE delivery costs, T+1 settlement)
result = Tantra.backtest(
    MyStrategy(),
    symbol="RELIANCE",
    exchange="NSE",
    start="2024-01-01",
    end="2024-12-31",
    cash=1_000_000,
).run()
print(result.metrics["final_equity"])
```

## Running them

```bash
# Paper trading (always works offline)
python examples/production/01_paper_trading.py --strategy sma_crossover --capital 100000

# Live trading (requires Dhan credentials)
python examples/production/02_live_trading_dhan.py --client-id XXX --access-token YYY --strategy sma_crossover

# Multi-account
python examples/production/03_multi_account.py --accounts config/accounts.yaml

# Monitoring
python examples/production/04_monitoring.py --port 9090

# Deployment config generation
python examples/production/05_deployment.py --output /etc/tantra/

# Multi-broker dispatch parity
python examples/production/06_multi_broker_dispatch.py --brokers zerodha,angelone,upstox
```

## Key concepts

1. **Adapter swap** — Same strategy code runs paper ↔ live by changing adapter config
2. **Risk guards** — Session-level limits (position, daily loss, margin) enforced before order send
3. **Idempotency** — `client_order_id` ensures safe retries; broker deduplication
4. **Reconciliation** — Periodic `positions()` vs broker `holdings()` drift check
5. **Graceful shutdown** — Cancel open orders, flatten positions (optional), persist state

## From paper to live

```
paper (fake adapter) → paper (real adapter, simulated fills) → live (real adapter, real fills)
     ↑                      ↑                              ↑
  offline              network                         real money
  deterministic        non-deterministic               requires monitoring
```
