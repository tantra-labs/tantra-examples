# 0005 — Categorised Screening, Universe & Rotation Examples

**Status**: Proposed

## 0. Executive Summary & Objective

Teach the new screening, QVM, universe and alert surfaces through runnable examples, and migrate the
examples package off its private universe mirror and string-built SQL onto tantra-data readers.

References: research [`trendlyne-screener-alerts-mcp.md`](../../../docs/research/trendlyne-screener-alerts-mcp.md);
root roadmap [`0007`](../../../docs/plans/0007-screener-taxonomy-and-alerts.md).
Depends on: [tantra-data 0007](../../../tantra-data/docs/plans/0007-instrument-master-index-membership.md),
[tantra-data 0008](../../../tantra-data/docs/plans/0008-screen-dsl-catalog-qvm.md),
[tantra-strategies 0002](../../../tantra-strategies/docs/plans/0002-universe-screen-context.md).

## 1. Context & Gaps Covered

Universe resolution now comes from the wheel (`tantra.markets.india.universes`: `resolve_universe`,
`UniverseUnavailable`; examples gaps 0004/0006 closed upstream) and supports only a few
hand-registered lists (nifty50, Alpha30, Bank Nifty). `pipeline/screeners.py`
(`ScreenerStep`, `MultibaggerScreener`, `ValueScreener`, `DividendYieldScreener`) builds DuckDB SQL
with a string `_asof_clause`. The data-backed, point-in-time universes come from
tantra-data plan 0007, surfaced through the wheel's `resolve_universe`.

## 2. Component Specifications & Phases

### Phase A — New examples (style: CLI `--asof/--top/--format symbols|json`, symbols on stdout, diagnostics on stderr)
- `examples/screening/09_sector_relative_value.py` (PE/PB vs sector median)
- `examples/screening/10_ma_cross_by_index.py` (golden/death cross within an index)
- `examples/screening/11_qvm_buckets.py` (QVM G/M/B buckets and combo labels with explanations)
- `examples/screening/12_catalog_browse.py` (list/run catalog presets by category)
- `examples/universes/10_midcap_momentum_rotation.py`
- `examples/strategies/` sector-rotation strategy using `ctx.universe` and `on_rebalance`.
- Chain TOMLs under `examples/screening/chains/` that reference catalog preset ids (consumed by `06_run_chain.py`).

### Phase B — Migration
- `resolve_universe` delegates to tantra-data `UniverseReader`; keeps `UniverseUnavailable` semantics.
- `pipeline/screeners.py` moves to tantra-data readers with parameterised SQL (no string-built clauses).

### Phase C — Gap hygiene
- Switch examples from the hand-registered wheel lists to data-backed `resolve_universe(name, as_of=...)` once tantra-data 0007 lands; no examples gap needs reopening.

## 3. Test Plan (TDD)

In `tests/`: `tests/unit` for argument parsing and migration shims, `tests/integration` over a seeded
fixture lakehouse, `tests/snapshots` golden outputs for every new example and chain; regression test
that no SQL in `pipeline/` is built by string interpolation.

## 4. Dependencies & Tier Notes

L6; examples use only public surfaces (`tantra` wheel, tantra-data readers). Examples for blocked
categories (shareholding, estimates) stay out until tantra-data gap 0024 closes.

## 5. Open Questions

- Fixture lakehouse size for deterministic goldens without bloating the repo.
