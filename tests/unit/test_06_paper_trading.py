"""basic/06_paper_trading: a seeded PaperSession round trip (plan 0003, T14.11).

The example runs the compiled paper-exchange engine in deterministic seeded
mode; the regression test asserts the report shape, the two-sided round-trip
fills, the wash back to starting equity, and that two runs with the same seed
are byte-identical.
"""

from __future__ import annotations

import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "examples" / "basic" / "06_paper_trading.py"


@pytest.fixture(scope="module")
def example():
    spec = importlib.util.spec_from_file_location("paper_trading", _PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(example):
    return example.run()


def test_report_shape(report):
    assert set(report) == {"seed", "orders", "fills", "equity", "cash", "positions"}
    assert report["seed"] == 7
    assert report["orders"]["limit_buy"].startswith("PAPER-")
    assert report["orders"]["market_sell"].startswith("PAPER-")


def test_round_trip_fills_both_sides(report):
    assert len(report["fills"]) == 2
    assert {f["side"] for f in report["fills"]} == {"BUY", "SELL"}
    for fill in report["fills"]:
        assert fill["instrument"] == "NSE:RELIANCE"
        assert Decimal(fill["quantity"]) == Decimal("10")
        assert Decimal(fill["price"]) == Decimal("100")


def test_round_trip_returns_to_starting_equity(report):
    assert Decimal(report["cash"]) == Decimal("1000000")
    assert Decimal(report["equity"]) == Decimal("1000000")
    assert report["positions"] == {"NSE:RELIANCE": "0"}


def test_output_is_deterministic_across_two_calls(example):
    first = json.dumps(example.run(), default=str)
    second = json.dumps(example.run(), default=str)
    assert first == second


def test_seeded_runs_reproduce_exactly(example):
    a = json.dumps(example.run(seed=42), default=str)
    b = json.dumps(example.run(seed=42), default=str)
    assert a == b


def test_main_writes_same_json_to_out_and_stdout(example, tmp_path, capsys):
    out = tmp_path / "paper.json"
    assert example.main(["--out", str(out)]) == 0
    stdout = capsys.readouterr().out
    assert stdout == out.read_text()
    assert {f["side"] for f in json.loads(stdout)["fills"]} == {"BUY", "SELL"}
