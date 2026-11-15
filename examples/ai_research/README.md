# 09 AI Research – the research loop on top of Tantra

The AI-research examples show the research loop layered on Tantra: natural-language
query → validated filter, autonomous backtesting, NL→strategy verification,
reinforcement learning, and the MCP tool gateway. There is no trading strategy
here. All ten scripts run offline and deterministic (`ScriptedFakeLlm`, no
network, no API keys); 02/04/05/07 run demos of the shipped `tantra.ai` wheel
surface while keeping the future-work design notes, and their not-yet-shipped
modules (`tantra.ai.autoresearch.*` / `verification.*` / `rl.*`) remain documented
design.

## At a glance

| #  | File                              | Strategy / focus | What you learn / what it would do                                                                  |
|----|-----------------------------------|------------------|----------------------------------------------------------------------------------------------------|
| 01 | `01_llm_research_analyst.py`      | —                | **Runnable.** NL question → validated screener filter via `ScriptedFakeLlm` + `KnowledgePack`      |
| 02 | `02_autoresearch_loop.py`         | —                | **Runnable demo.** Hypothesis → `translate_query` → `guard_llm_decision` loop; the full loop (Faiss + Parquet journal) is documented design |
| 03 | `03_nl_screener.py`               | —                | **Runnable.** NL query → strict screener filter → historical backtest                               |
| 04 | `04_nl_to_strategy.py`            | —                | **Runnable demo.** NL → validated filter via `tantra.ai.ask` + the `tantra.screener` catalog; the verification sandbox is documented design |
| 05 | `05_rl_training.py`               | —                | **Runnable design notes.** RL trainer design printed (`torch` + `gymnasium` optional extras, never imported) |
| 06 | `06_mcp_integration.py`           | —                | **Runnable.** Enumerate the static MCP tools from `schema/mcp/mcp_tools.json`                      |
| 07 | `07_natural_language_critique.py` | —                | **Runnable design notes.** prints the critique pitfalls + a tiny `tantra.ai` ask demo; the critic is future work |
| 09 | `09_typed_llm_decision.py`        | —                | **Runnable.** Typed `LlmDecision` (veto / size-down) applied to an order intent; size increases are rejected; Journal v1 audit records |
| 10 | `10_claude_autonomous_quant.py`   | —                | **Runnable.** MCP quant agent workflow: inspect the MCP tool schema + indicator catalog, propose a mean-reversion hypothesis, backtest it, evaluate with the Deflated Sharpe Ratio; offline via `ScriptedFakeLlm` |
| 11 | `11_deterministic_ai_replay.py`   | —                | **Runnable.** Cryptographic prompt replayer: record N AI decisions to a SHA-256 prompt cache + Journal v1 NDJSON, then replay from disk with no API calls |
| 12 | `12_ai_drawdown_refinement.py`    | —                | **Runnable.** AI strategy auto-enhancer: diagnose a ≥12% drawdown streak, propose an ADX trend filter, run it through the `decision_guard` guard rules, and re-evaluate out-of-sample with DSR |

Slot 08 is intentionally unused (reserved; numbers are not reused or shifted).

## Pitfalls checklist

Every numbered script in this directory has a `Pitfalls::` section in its module docstring
(enforced by `tests/unit/test_pitfalls_sections.py`). For the four design-documentation scripts
(02/04/05/07) it lists the traps the future code must defend against; the scripts themselves run
deterministic demos of the shipped `tantra.ai` surface. The recurring AI-research
traps: an LLM may already know how a historic date turned out (training-data look-ahead); output
is non-deterministic, so store the prompt, response and seed; any text pasted into a prompt or
returned by a tool is untrusted; model output is parsed by a grammar and never executed; a loop of
generated strategies is a multiple-testing problem (count every trial, keep a holdout); RL needs a
time split, costs in the reward and many seeds; and the fake backends here prove plumbing, not a
model. For the general treatment see
[Avoiding backtest biases](https://tantra-labs.github.io/tantra/book/backtesting/avoiding_backtest_biases.html).

## The `tantra.ai` wheel surface (offline; gap 0002 closed)

| Module                                   | Symbols                                          | Runs offline? |
|------------------------------------------|--------------------------------------------------|---------------|
| `tantra.ai.llm.provider`                 | `LlmPort`, `ScriptedFakeLlm`                     | ✅             |
| `tantra.ai.knowledge`                    | `KnowledgePack`, `build_knowledge_pack`          | ✅             |
| `tantra.ai.ask`                          | `translate_query`, `AskResult`, `build_system_prompt` | ✅             |
| `tantra.ai.decision`                     | `guard_llm_decision`, `LlmDecision`, `DecisionKind` | ✅             |
| `schema/mcp/mcp_tools.json`              | MCP read-only tool catalog                       | ✅             |
| `tantra.ai.autoresearch.*` (future)      | **Design only** (loop.py, hypothesis.py, evaluator.py, journal.py) | ❌ |
| `tantra.ai.verification.*` (future)      | **Design only** (critic.py, nl_to_strategy.py, regime_report.py) | ❌ |
| `tantra.ai.rl.*` (future)                | **Design only** (environment.py, agent.py, policies.py, trainer.py) | ❌ |

The CLI's `tantra screener ask` defaults to `ScriptedFakeLlm` — swap a real
provider (`LlmPort` impl) only when you have `openai`/`anthropic`/`litellm`
installed and an API key set.

## Running them

```bash
python examples/ai_research/01_llm_research_analyst.py --query "rsi below 30" --fake-response "rsi < 30"
python examples/ai_research/06_mcp_integration.py
python examples/ai_research/09_typed_llm_decision.py
python examples/ai_research/10_claude_autonomous_quant.py --underlying RELIANCE --seed 42
python examples/ai_research/11_deterministic_ai_replay.py --decisions 10 --seed 42
python examples/ai_research/12_ai_drawdown_refinement.py --seed 42 --out refinement.json
pytest tests/unit -q -k "llm_research or mcp_integration or typed_llm or claude_autonomous or deterministic_ai_replay or ai_drawdown"
```

## Architecture references

- Gap 0002 closed: the wheel ships `tantra.ai` (ask/decision/knowledge/llm.provider); the `_kernel/ai/` mirror, `fake_llm.py` and `decision_guard.py` were deleted and every consumer retargeted to the wheel.
- `.agents/AGENTS.md` §5.5 — NoFX idea inheritance: untrusted AI principle, closed decision grammar, cryptographic replayability.
