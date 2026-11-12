# mirror: kernel-verbatim port (gap 0002: tantra-agent surface)

from __future__ import annotations

from tantra_examples._kernel.ai.ask import (
    AskResult,
    FilterParseError,
    QueryTranslationError,
    build_system_prompt,
    parse_filters,
    translate_query,
)
from tantra_examples._kernel.ai.decision import (
    DecisionKind,
    GuardedDecision,
    LlmDecision,
    apply_llm_decision,
    guard_llm_decision,
    is_protective_exit,
    validate_llm_decision,
)
from tantra_examples._kernel.ai.knowledge import (
    FEW_SHOT_EXAMPLES,
    FILTER_GRAMMAR_EBNF,
    KnowledgePack,
    build_knowledge_pack,
)
from tantra_examples._kernel.ai.llm.provider import (
    LlmPort,
    ScriptedFakeLlm,
)

__all__ = [
    "FEW_SHOT_EXAMPLES",
    "FILTER_GRAMMAR_EBNF",
    "AskResult",
    "DecisionKind",
    "FilterParseError",
    "GuardedDecision",
    "KnowledgePack",
    "LlmDecision",
    "LlmPort",
    "QueryTranslationError",
    "ScriptedFakeLlm",
    "apply_llm_decision",
    "build_knowledge_pack",
    "build_system_prompt",
    "guard_llm_decision",
    "is_protective_exit",
    "parse_filters",
    "translate_query",
    "validate_llm_decision",
]
