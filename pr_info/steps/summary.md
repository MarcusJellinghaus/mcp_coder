# Issue #819: Token Usage Collection Across All Providers + iCoder Cache Display

## Goal

Collect token usage consistently from all LLM providers (Claude CLI, LangChain) and display cache hit percentage in icoder's status bar.

## Current State

- **Claude CLI**: Already emits `input_tokens`, `output_tokens`, `cache_read_input_tokens` in "done" event `usage` dict. Works end-to-end.
- **LangChain**: All three paths (`_ask_text`, `_ask_text_stream`, `run_agent`/`run_agent_stream`) discard `usage_metadata` from `AIMessage`.
- **icoder**: `TokenUsage` tracks raw input/output counts only; no cache info. Display: `↓1.2k ↑800 | total: ↓5k ↑3k`.

## Architecture / Design Changes

### 1. New shared type: `UsageInfo` TypedDict (`llm/types.py`)

Provider-agnostic usage type with `total=False` (all fields optional):
```
input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens
```
This is the contract between providers and consumers. Lives in `llm/types.py` (LLM layer, not UI layer) per issue Decision #3.

### 2. LangChain usage extraction helper (`langchain/_usage.py`)

Single `_extract_usage(ai_msg)` helper maps LangChain's `usage_metadata` → `UsageInfo` dict. Used in all 4 LangChain code paths to avoid duplicating the nested-dict traversal (`input_token_details.cache_read` → `cache_read_input_tokens`, etc.). A companion `_sum_usage()` helper adds two usage dicts for agent multi-step summing. Both live in a dedicated `_usage.py` submodule (not in `langchain/__init__.py`) to avoid circular-import risk between `__init__.py` and `agent.py`.

Note: `cache_creation_input_tokens` flows into `StreamEvent["usage"]` and `raw_response["usage"]` but is NOT extracted into `TokenUsage` or displayed. It is captured for future analysis/logging.

### 3. Data flow (unchanged architecture, new data)

```
Provider → StreamEvent{"type":"done", "usage": UsageInfo} → AppCore.stream_llm() → TokenUsage → UI
```

No new interfaces, protocols, or plumbing. The "done" event already carries a `usage` dict; we just ensure LangChain populates it (like Claude CLI already does) and icoder reads the cache fields from it.

### 4. icoder display change

Before: `↓1.2k ↑800 | total: ↓5k ↑3k`
After:  `↓1.2k ↑800 cache:45% | total: ↓5k ↑3k cache:52%`

Cache percentage hidden entirely when data unavailable (Decision #6).

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/types.py` | Add `UsageInfo` TypedDict, export in `__all__` |
| `src/mcp_coder/llm/__init__.py` | Re-export `UsageInfo` |
| `src/mcp_coder/llm/providers/langchain/_usage.py` | **New file.** Contains `_extract_usage()` and `_sum_usage()` helpers |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Import helpers from `_usage`; use in `_ask_text`, `_ask_text_stream` |
| `src/mcp_coder/llm/providers/langchain/agent.py` | Sum usage in `run_agent()` stats and `run_agent_stream()` done event |
| `src/mcp_coder/icoder/core/types.py` | Add cache fields to `TokenUsage`, update `update()` signature, update `display_text()` |
| `src/mcp_coder/icoder/core/app_core.py` | Pass `cache_read_input_tokens` from done event to `TokenUsage.update()` |

## Test Files Modified

| File | Change |
|------|--------|
| `tests/llm/test_types.py` | Test `UsageInfo` TypedDict existence and fields |
| `tests/icoder/test_types.py` | Test `TokenUsage` with cache data, `display_text()` with/without cache |
| `tests/icoder/test_app_core.py` | Test cache data flows through `stream_llm()` to `token_usage` |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Test `_ask_text` includes usage in `raw_response` |
| `tests/llm/providers/langchain/test_langchain_streaming.py` | Test `_ask_text_stream` emits usage in done event |
| `tests/llm/providers/langchain/test_langchain_agent.py` | Test `run_agent` includes usage in stats |
| `tests/llm/providers/langchain/test_langchain_agent_streaming.py` | Test `run_agent_stream` emits usage in done event |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | `UsageInfo` TypedDict in `llm/types.py` + exports + tests | `feat(llm): add UsageInfo TypedDict` |
| 2 | `TokenUsage` cache fields + display_text cache% + tests | `feat(icoder): add cache tracking to TokenUsage` |
| 3 | AppCore passes cache data to TokenUsage + tests | `feat(icoder): wire cache usage through AppCore` |
| 4 | LangChain `_ask_text` + `_ask_text_stream` usage extraction + tests | `feat(langchain): extract usage from text paths` |
| 5 | LangChain agent usage summing (`run_agent` + `run_agent_stream`) + tests | `feat(langchain): sum usage across agent steps` |

## Decisions (from issue)

| # | Decision | Rationale |
|---|----------|-----------|
| 3 | `UsageInfo` in `llm/types.py` | Clean separation, KISS |
| 5 | Display: `↓1.2k ↑800 cache:45% \| total: ↓5k ↑3k cache:52%` | Compact |
| 6 | Hide `cache:XX%` when unavailable | Cleaner than placeholders |
| 8 | No cost display | Inconsistent across providers |
| 9 | Agent: sum all LLM calls | Total consumption per request |
| 10 | Cache % = `cache_read / input_tokens` | Savings metric |
