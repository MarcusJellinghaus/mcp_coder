# Step 4: LangChain text paths — extract usage from `_ask_text` and `_ask_text_stream`

> **Context**: See `pr_info/steps/summary.md` for full issue context. This is step 4 of 5.

## LLM Prompt

```
Implement step 4 of issue #819 (pr_info/steps/summary.md).
Add _extract_usage() and _sum_usage() helpers to the langchain provider package.
Use _extract_usage() in _ask_text (→ raw_response["usage"]) and _ask_text_stream (→ done event usage).
Write tests first (TDD), then implement. Run all three checks after.
```

## WHERE

- **Modify**: `src/mcp_coder/llm/providers/langchain/__init__.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_provider.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_streaming.py`

## WHAT

### New helper functions (module-private)

```python
def _extract_usage(ai_msg: Any) -> dict[str, int]:
    """Extract UsageInfo-shaped dict from a LangChain AIMessage's usage_metadata."""

def _sum_usage(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    """Sum two usage dicts field-by-field. Used for agent multi-step summing."""
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

```python
keys = {"input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"}
return {k: a.get(k, 0) + b.get(k, 0) for k in keys if a.get(k, 0) + b.get(k, 0) > 0}
```

## ALGORITHM — `_ask_text_stream()` change

```python
last_chunk = None          # track last chunk with usage_metadata
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
2. **`test_extract_usage_no_metadata`** — mock `AIMessage` without `usage_metadata`, verify empty dict returned
3. **`test_extract_usage_no_cache_details`** — `usage_metadata` has tokens but no `input_token_details`, verify only `input_tokens`/`output_tokens` extracted
4. **`test_sum_usage_basic`** — sum two dicts, verify correct addition
5. **`test_sum_usage_partial_keys`** — one dict has cache, other doesn't, verify correct merge
6. **`test_ask_text_includes_usage`** — mock `chat_model.invoke()` returning `AIMessage` with `usage_metadata`, verify `raw_response["usage"]` populated

### `tests/llm/providers/langchain/test_langchain_streaming.py`

7. **`test_text_stream_done_event_includes_usage`** — mock chunks where last chunk has `usage_metadata`, verify done event has `usage` dict with correct fields
8. **`test_text_stream_done_event_no_usage_metadata`** — mock chunks without `usage_metadata`, verify done event has empty `usage` dict

## COMMIT

```
feat(langchain): extract token usage from text and stream paths (#819)
```
