# 0002 — tantra-wheel-ai-provider-surface

**Status**: open — blocked
**Owning repo**: `tantra-agent` (autonomous research loop, LLM adapters, MCP server) and
`tantra-ffi` (wheel surface).

## Symptom
`honba.ai.{ask, decision, llm.provider, autoresearch}` have no `tantra` equivalent, so the
port cannot ship real LLM-backed flows offline or against the agent runtime.

## What stands in (scripted/mirror paths)
* `tantra_examples/_kernel/ai/` — kernel-verbatim mirror of the AI surface:
  `ask.py` (query → filter translation), `decision.py` (typed `LlmDecision` +
  `guard_llm_decision`), `knowledge.py` (grammar/knowledge packs), `llm/provider.py`
  (`LlmPort` + `ScriptedFakeLlm`). `# mirror: kernel-verbatim port (gap 0002)`.
* `tantra_examples/fake_llm.py` — the harness-side `LlmPort` + `ScriptedFakeLlm`
  (deterministic scripted provider used by every offline example).
* `tantra_examples/decision_guard.py` — fail-closed, reduce-only guard wrapping the
  kernel decision core (approve / veto / size_down), so scripted LLM decisions flow
  through the same assertions the engine would enforce.
* `tantra_examples/screening/nl_support.py` — natural-language screener translation with
  a scripted provider fallback.
* Design-only scripts, all `pytest.skip`-blocked with `"Design-only (gap 0002)"`:
  `examples/ai_research/02_autoresearch_loop.py`, `04_nl_to_strategy.py`,
  `05_rl_training.py`, `07_natural_language_critique.py`.

## How to close
Provide the wheel/agent surface (`tantra.ai.llm.provider`, decision parsing, MCP bridge —
`tantra-agent-mcp`), then delete `_kernel/ai/` and `fake_llm.py`'s provider shim, retarget
the imports, un-skip the design-only scripts, and drop the `decision_guard.py` wrapper
where the engine's guard ships.

## Blocker analysis (2026-11-14)

Verified: `_kernel/ai/` depends on `_kernel.screener.catalog`, `_kernel.wire.screener`,
`_kernel.ai.{knowledge, llm.provider, ask}`, and `tantra_examples.decision_guard` — i.e.
the AI surface sits **on top of** the `_kernel` screener/wire domain sub-slices (gap 0006).
Those `screener`/`wire` surfaces must ship in the wheel first (ex 0006 sub-slices), and no
`tantra.ai` wheel namespace exists today, so this gap cannot close until both land. Closure
order: ex 0006 `screener`/`wire` → `tantra.ai` namespace (tantra-agent/ffi) → delete
`_kernel/ai/` + the `fake_llm.py` provider shim → un-skip the design-only scripts.
