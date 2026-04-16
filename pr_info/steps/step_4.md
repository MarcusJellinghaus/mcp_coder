# Step 4: LangChain text paths — extract usage from `_ask_text` and `_ask_text_stream`

> **Context**: See `pr_info/steps/summary.md` for full issue context. This is step 4 of 5.

## LLM Prompt

```
Implement step 4 of issue #819 (pr_info/steps/summary.md).
Create a new _usage.py submodule under the langchain provider package containing
_extract_usage() and _sum_usage() helpers. Use _extract_usage() in _ask_text
(→ raw_response["usage"]) and _ask_text_stream (→ done event usage).
Write tests first (TDD), then implement. Run all three checks after.
```

## WHERE

- **Create**: `src/mcp_coder/llm/providers/langchain/_usage.py` (new file containing `_extract_usage` and `_sum_usage`)
- **Modify**: `src/mcp_coder/llm/providers/langchain/__init__.py` (import helpers from `_usage` for use in `_ask_text` and `_ask_text_stream`)
- **Modify**: `tests/llm/providers/langchain/test_langchain_provider.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_streaming.py`

## WHAT

### New helper functions (in `_usage.py`, module-private)

Helpers live in a dedicated `_usage.py` submodule (NOT in `langchain/__init__.py`) to avoid circular-import risk between `langchain/__init__.py` and `agent.py`.

```python
from mcp_coder.llm.types import UsageInfo

def _extract_usage(ai_msg: Any) -> UsageInfo:
    """Extract UsageInfo-shaped dict from a LangChain AIMessage's usage_metadata."""

def _sum_usage(a: UsageInfo, b: UsageInfo) -> UsageInfo:
    """Sum two UsageInfo dicts field-by-field. Used for agent multi-step summing."""
```

### `_ask_text()` change

After `ai_msg = chat_model.invoke(lc_messages)`, extract usage and add to `raw` dict:
```python
raw["usage"] = _extract_usage(ai_msg)
```

### `_ask_text_stream()` change

Track the last chunk that has `usage_metadata`. After the streaming loop, emit usage in the done event:
```python
yield {"type": "done", "session_id": session_id, "usage": _extract_usage(last_chunk_with_usage)}
```

The `last_chunk` tracking and modified `yield done` go inside the existing `try:` block (inside the `for chunk in chat_model.stream(...)` loop for tracking, and replacing the line `yield {"type": "done", "session_id": session_id, "usage": {}}` after the loop). The error/timeout branches are unchanged.

## ALGORITHM — `_extract_usage(ai_msg)`

```python
meta = getattr(ai_msg, "usage_metadata", None) or {}
details = meta.get("input_token_details") or {}
usage = {}
for key in ("input_tokens", "output_tokens"):
    if key in meta:
        usage[key] = meta[key]
if "cache_read" in details:
    usage["cache_read_input_tokens"] = details["cache_read"]
if "cache_creation" in details:
    usage["cache_creation_input_tokens"] = details["cache_creation"]
return usage
```

## ALGORITHM — `_sum_usage(a, b)`

Always include all 4 keys with `0` default. Symmetric with `_extract_usage`; the display layer already gates `cache:XX%` on `cache_read > 0`, so emitting zeros is safe.

Docstring must note: "Always returns all 4 keys (zero-default). Symmetric contract — display layer gates on `cache_read > 0`." This prevents future "optimization" back to dropping zeros.

```python
def _sum_usage(a: UsageInfo, b: UsageInfo) -> UsageInfo:
    keys = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    return {k: a.get(k, 0) + b.get(k, 0) for k in keys}
```

## ALGORITHM — `_ask_text_stream()` change

Track ANY chunk with non-empty `usage_metadata` as `last_chunk` (last-wins). Do NOT assume usage only appears on the final chunk — some providers emit usage on a middle chunk and then send additional chunks without usage.

```python
last_chunk = None          # last-wins: any chunk with non-empty usage_metadata
for chunk in chat_model.stream(lc_messages):
    if getattr(chunk, "usage_metadata", None):
        last_chunk = chunk
    # ... existing yield logic ...

# In done event:
usage = _extract_usage(last_chunk) if last_chunk else {}
yield {"type": "done", "session_id": session_id, "usage": usage}
```

## DATA

LangChain `usage_metadata` structure (from `AIMessage`):
```python
{
    "input_tokens": 1200,
    "output_tokens": 800,
    "total_tokens": 2000,
    "input_token_details": {
        "cache_read": 540,
        "cache_creation": 100,
    }
}
```

Mapped to `UsageInfo`:
```python
{
    "input_tokens": 1200,
    "output_tokens": 800,
    "cache_read_input_tokens": 540,
    "cache_creation_input_tokens": 100,
}
```

## TESTS

### `tests/llm/providers/langchain/test_langchain_provider.py`

1. **`test_extract_usage_full_metadata`** — mock `AIMessage` with full `usage_metadata` including `input_token_details`, verify all 4 fields extracted
2. **`test_extract_usage_no_metadata`** — parameterized test covering 3 cases (use `pytest.mark.parametrize` or 3 explicit asserts): (a) attribute absent on message, (b) `usage_metadata is None`, (c) `usage_metadata == {}`. All three should return `{}`.
3. **`test_extract_usage_no_cache_details`** — `usage_metadata` has tokens but no `input_token_details`, verify only `input_tokens`/`output_tokens` extracted
4. **`test_sum_usage_basic`** — sum two dicts, verify correct addition
5. **`test_sum_usage_partial_keys`** — one dict has cache, other doesn't, verify correct merge
6. **`test_ask_text_includes_usage`** — mock `chat_model.invoke()` returning `AIMessage` with `usage_metadata`, verify `raw_response["usage"]` populated

### `tests/llm/providers/langchain/test_langchain_streaming.py`

7. **`test_text_stream_done_event_includes_usage`** — mock chunks where last chunk has `usage_metadata`, verify done event has `usage` dict with correct fields
8. **`test_text_stream_done_event_no_usage_metadata`** — mock chunks without `usage_metadata`, verify done event has empty `usage` dict
9. **`test_text_stream_usage_on_middle_chunk`** — mock chunks where a middle chunk carries `usage_metadata` and the final chunk does NOT; verify usage is still extracted correctly (regression guard for last-wins tracking)

10. **`test_ask_text_stream_usage_flows_to_raw_response`** — end-to-end test that exercises `_ask_text_stream()` through `ResponseAssembler` via the public `ask_with_provider(..., provider_stream=True)` path (or directly via the assembler). Assert that when the stream yields a `done` event with non-empty `usage` containing all 4 fields, the final `LLMResponseDict.raw_response["usage"]` contains all 4 fields (including `cache_creation_input_tokens`). Note: `tests/llm/test_types.py::test_response_assembler_done_event` already covers 2 fields (`input_tokens`, `output_tokens`) flowing through `ResponseAssembler`; this new test extends coverage to all 4 fields via the LangChain streaming path.

## COMMIT

```
feat(langchain): extract token usage from text and stream paths (#819)
```
