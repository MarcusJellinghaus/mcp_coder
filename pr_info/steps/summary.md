# feat(langchain): Add Real Streaming for LangChain Agent Mode

**Issue:** #603
**Branch:** feat/603-langchain-agent-streaming

## Problem

When `mcp_config` is present, `ask_langchain_stream()` calls blocking `ask_langchain()`,
waits for full completion, then yields one `text_delta` with the entire response + one `done` event.
Users see no output until the entire agent execution finishes.

## Solution

Replace the blocking fallback with real streaming using LangChain's `astream_events(version="v2")` API,
bridged to the sync `Iterator[StreamEvent]` interface via `threading.Thread` + `queue.Queue`.

## Architecture / Design Changes

### Async-to-Sync Bridge (new pattern in `__init__.py`)

```
ask_langchain_stream()  [sync generator]
  │
  ├── mcp_config=None → _ask_text_stream()  [existing, unchanged]
  │
  └── mcp_config set  → thread+queue bridge  [NEW]
        │
        │  threading.Thread(target=asyncio.run, args=(_run(),))
        │  queue.Queue[StreamEvent | None]  ← sentinel None = done
        │  threading.Event for cancellation
        │
        └── _run() calls run_agent_stream()  [NEW async generator in agent.py]
              │
              └── agent.astream_events(input, version="v2")
                    ├── on_chat_model_stream → text_delta
                    ├── on_tool_start        → tool_use_start
                    ├── on_tool_end          → tool_result
                    ├── all events           → raw_line
                    └── completion           → done (with history stored)
```

### Timeout Strategy (2 lines, not 2 classes)

- **No-progress**: `q.get(timeout=600)` — raises `queue.Empty` after 10 min of silence
- **Overall cap**: `time.monotonic() - start > 3600` — checked each iteration

### ResponseAssembler Extension (in `types.py`)

- New `_tool_trace: list[StreamEvent]` accumulates `tool_use_start` and `tool_result` events
- Exposed as `tool_trace` in `result()["raw_response"]`
- No correlation logic — consumers match `tool_call_id` themselves

### No Shared Helper Extraction

Tool loading (~15 lines) is inlined in both `run_agent()` and `run_agent_stream()`.
Simpler than a shared helper; trivial to extract later if they diverge.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/types.py` | Extend `ResponseAssembler` with `_tool_trace` accumulation |
| `tests/llm/test_types.py` | Add tests for tool_trace in ResponseAssembler |
| `src/mcp_coder/llm/providers/langchain/agent.py` | Add `run_agent_stream()` async generator |
| `tests/llm/providers/langchain/test_langchain_streaming.py` | Add streaming agent tests, replace fallback tests |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Replace agent fallback with thread+queue bridge |

## Files NOT Modified (confirmed)

- `src/mcp_coder/llm/interface.py` — already yields `Iterator[StreamEvent]`, no changes needed
- `src/mcp_coder/llm/types.py` StreamEvent type alias — `tool_use_start`/`tool_result` already documented
- `tests/llm/providers/langchain/conftest.py` — existing mocks sufficient

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Extend `ResponseAssembler` with tool_trace (TDD) | `feat(types): add tool_trace accumulation to ResponseAssembler` |
| 2 | Add `run_agent_stream()` async generator in agent.py (TDD) | `feat(agent): add run_agent_stream async generator with astream_events` |
| 3 | Replace agent fallback with thread+queue bridge in `__init__.py` (TDD) | `feat(langchain): replace agent streaming fallback with real streaming` |
| 4 | Add timeout and cancellation handling (TDD) | `feat(langchain): add timeout and cancellation to agent streaming` |
