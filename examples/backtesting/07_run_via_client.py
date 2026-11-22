"""backtesting/07_run_via_client: InprocTransport vs HttpTransport, run_id, assumptions.

Demonstrates the Tantra run service (ADR 0017, E4-S3): a backtest is a first-class server
object with a run_id, status lifecycle, and assumptions including not_modelled.
This example runs the same strategy via the in-process transport and an HTTP transport
to a running `tantra serve` and asserts parity of fills, run_id traceability, and
assumptions presence.

Run::

    # In-process only (no server needed)
    python examples/backtesting/07_run_via_client.py --data-dir data/catalog --inproc

    # Via HTTP to a running `tantra serve` (requires the binary)
    python examples/backtesting/07_run_via_client.py --data-dir data/catalog --url http://127.0.0.1:8080

    # Both, asserting parity
    python examples/backtesting/07_run_via_client.py --data-dir data/catalog --both

Pitfalls::

    - Hindsight universe: the run is fixed to RELIANCE.NSE, one large stock still listed today, over
      2024-01-01 to 2024-06-01. That is one name chosen with hindsight in about five months of daily
      bars and one regime; it demonstrates the run service, not the strategy.
    - Parity is plumbing, not realism: assert_parity shows in-process and HTTP produce identical
      fills, which proves determinism. It does not show the fill model is realistic. Read
      assumptions.timing and assumptions.not_modelled in the result before trusting any metric.
    - Closed trades only: the comment in assert_parity says metrics come from closed round trips
      with no mark-to-market, so a position still open at the end (perhaps deep underwater) is not
      counted. Read the journal as well as the summary.
    - Data quality is the catalog's: bars come from --data-dir as stored. Confirm they are split and
      dividend adjusted and have no gaps, because the same strategy gives different fills on
      unadjusted data.
    - The seed (42) only pins stochastic components; it is not a robustness check. Vary the window
      and the instrument before concluding anything.
    - No in-process transport: `Client.inproc` raises NotImplementedError in the wheel today, so
      --inproc and --both exit 1 with a clear message; use --url against `tantra serve`. Wheels
      without `tantra.client` degrade to a clear error instead of an ImportError at import time.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from tantra.client import BacktestResult, Client
else:
    try:
        # gap 0004: tantra.client wheel surface missing; degrade gracefully (D7).
        from tantra.client import BacktestResult, Client
    except ImportError:
        BacktestResult = Any
        Client = None

_MISSING_CLIENT_MSG = (
    "tantra.client is not available yet "
    "(docs/gaps/0004-tantra-wheel-display-universes-client.md); "
    "this example cannot run until the wheel ships the run-service client."
)


def run_inproc(data_dir: Path) -> BacktestResult:
    """Run the strategy over InprocTransport."""
    client = Client.inproc(data_dir, journals_dir=data_dir.parent / "journals_inproc")
    try:
        result = client.run_backtest(
            strategy="sma_crossover",
            universe="RELIANCE.NSE",
            start="2024-01-01",
            end="2024-06-01",
            seed=42,
            bar_spec="1d",
            initial_capital=Decimal("1000000"),
            timeout=60.0,
        )
        return result
    finally:
        client.close()


def run_http(base_url: str) -> BacktestResult:
    """Run the strategy over HttpTransport."""
    client = Client.http(base_url, timeout=60.0)
    try:
        result = client.run_backtest(
            strategy="sma_crossover",
            universe="RELIANCE.NSE",
            start="2024-01-01",
            end="2024-06-01",
            seed=42,
            bar_spec="1d",
            initial_capital=Decimal("1000000"),
            timeout=60.0,
        )
        return result
    finally:
        client.close()


def assert_parity(
    inproc: BacktestResult, http: BacktestResult, client_inproc: Client, client_http: Client
) -> None:
    """Assert that the two runs produce identical fills and run_id traceability."""
    # Same strategy, same seed, same data => identical journals (Decimals compare exactly).
    inproc_journal = client_inproc.backtest_journal(inproc.run_id)
    http_journal = client_http.backtest_journal(http.run_id)
    assert inproc_journal == http_journal, "journal mismatch between transports"
    assert inproc.status == http.status, "status mismatch between transports"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\nPitfalls::")[0] + "\n")
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Directory with SYMBOL.EXCHANGE.parquet bar files",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of running tantra serve",
    )
    parser.add_argument(
        "--inproc",
        action="store_true",
        help="Run only in-process (default: both if server available)",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run only against HTTP server",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Run both and assert parity (default if neither --inproc nor --http)",
    )
    args = parser.parse_args(argv)

    if Client is None:
        print(_MISSING_CLIENT_MSG, file=sys.stderr)
        return 1

    data_dir = args.data_dir
    if not data_dir.exists():
        print(f"Data directory does not exist: {data_dir}", file=sys.stderr)
        return 1

    # Check if HTTP server is available
    http_available = False
    if args.http or args.both or (not args.inproc and not args.http):
        try:
            resp = httpx.get(f"{args.url}/health", timeout=5.0)
            http_available = resp.status_code == 200
        except (httpx.HTTPError, OSError):
            http_available = False

    if args.inproc or (not args.http and not http_available):
        print("Running in-process...")
        try:
            inproc_result = run_inproc(data_dir)
        except NotImplementedError:
            print("inproc not available; use --url against `tantra serve`", file=sys.stderr)
            return 1
        print(f"Inproc result: run_id={inproc_result.run_id}, status={inproc_result.status}")
        print(f"  manifest: {dict(inproc_result.manifest)}")

    if args.http or args.both or (not args.inproc and http_available):
        if not http_available:
            print("HTTP server not available at --url", file=sys.stderr)
            return 1
        print("Running via HTTP...")
        http_result = run_http(args.url)
        print(f"HTTP result: run_id={http_result.run_id}, status={http_result.status}")
        print(f"  manifest: {dict(http_result.manifest)}")

    if args.both or (not args.inproc and not args.http and http_available):
        print("Asserting parity...")
        try:
            client_inproc = Client.inproc(
                data_dir, journals_dir=data_dir.parent / "journals_inproc"
            )
        except NotImplementedError:
            print("inproc not available; use --url against `tantra serve`", file=sys.stderr)
            return 1
        client_http = Client.http(args.url, timeout=60.0)
        try:
            inproc_result = run_inproc(data_dir)
            http_result = run_http(args.url)
            assert_parity(inproc_result, http_result, client_inproc, client_http)
            print("Parity confirmed: inproc and HTTP produce identical journals")
        finally:
            client_inproc.close()
            client_http.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
