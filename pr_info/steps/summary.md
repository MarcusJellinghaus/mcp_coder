# Issue #897 — Fix langchain tool result rendering + enhance event logging

## Problem

Langchain tool results render as ugly pydantic repr strings in iCoder and CLI output.
`str(ToolMessage(...))` in `agent.py:530-548` produces the pydantic `__repr_str__`
instead of extracting the actual tool content.

**Current:** `content=[{'type': 'text', 'text': 'true', 'id': 'lc_8c8dd727-...'}] name='save_file' ...`
**Expected:** `{"result": true}`

## Scope — 2 changes

1. **Fix langchain tool output extraction** (`agent.py`) — Replace `str(output)` with
   cascading content extraction from the ToolMessage object.
2. **Enhance iCoder event log** (`app_core.py`) — Log stream events (excluding `raw_line`)
   to JSONL for debugging/replay.

## Architecture / Design Changes

**No new modules, no new abstractions.** All changes are local modifications to existing code:

- **Langchain provider layer** (`agent.py`): The `on_tool_end` handler gains inline extraction
  logic. The fix stays in the provider where ToolMessage→StreamEvent conversion happens —
  the renderer remains provider-agnostic. Uses `hasattr`-based duck typing to avoid importing
  `ToolMessage`.
- **iCoder core layer** (`app_core.py`): One-line addition to the `stream_llm()` loop —
  forwards each stream event (except `raw_line`) to the existing `EventLog.emit()` method.
  No new config, no feature flag. The `EventLog` class itself is unchanged.
- **No renderer changes** — `stream_renderer.py` already handles JSON strings via
  `json.loads()` → `_render_output_value()`. The fix feeds it proper JSON from upstream.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/agent.py` | Replace `str(output)` with cascading extraction |
| `src/mcp_coder/icoder/core/app_core.py` | Add `event_log.emit("stream_event", ...)` in loop |
| `tests/llm/providers/langchain/test_langchain_agent_streaming.py` | Add tests for extraction cases |
| `tests/icoder/test_app_core.py` | Add test for stream event logging |

## Implementation Steps

| Step | Description |
|------|-------------|
| 1 | Fix langchain tool output extraction (TDD: tests first, then `agent.py` fix) |
| 2 | Enhance iCoder stream event logging (TDD: test first, then `app_core.py` change) |
