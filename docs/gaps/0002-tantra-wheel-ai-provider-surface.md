# 0002 — tantra-wheel-ai-provider-surface

**Status**: open
**Owning repo**: `tantra-agent` (autonomous research loop, LLM adapters, MCP server) and
`tantra-ffi` (wheel surface).

## Symptom
`honba.ai.{ask, decision, llm.provider, autoresearch}` have no `tantra` equivalent, so the
port cannot ship real LLM-backed flows offline or against the agent runtime.

## What stands in (scripted/mirror paths)
* `tantra_examples/fake_llm.py` — `LlmPort` + `ScriptedFakeLlm` (deterministic scripted
  provider used by every offline example).
* `tantra_examples/decision_guard.py` — kernel-verbatim decision grammar (approve /
  veto / size_down) so scripted LLM decisions flow through the same assertions the engine
  would enforce.
* `tantra_examples/screening/nl_support.py` — natural-language screener translation with a
  scripted provider fallback.
* `02_autoresearch_loop` remains design-only in the source repo and stays deferred; its
  tests skip until the `tantra-agent` loop ships (pytest.skip + this gap).

## How to close
Provide the wheel/agent surface (`tantra.ai.llm.provider`, decision parsing, MCP bridge —
`tantra-agent-mcp`), then delete `fake_llm.py`'s provider shim and retarget the D5 imports.
