# Step 3: Wire cache usage through AppCore

> **Context**: See `pr_info/steps/summary.md` for full issue context. This is step 3 of 5.

## LLM Prompt

```
Implement step 3 of issue #819 (pr_info/steps/summary.md).
Update AppCore.stream_llm() to extract cache_read_input_tokens from the done event
and pass it to TokenUsage.update(). Write tests first (TDD), then implement.
Run all three checks after.
```

## WHERE

- **Modify**: `src/mcp_coder/icoder/core/app_core.py`
- **Modify**: `tests/icoder/test_app_core.py`

## WHAT

In `AppCore.stream_llm()`, the existing code (lines 91-95) already extracts `input_tokens` and `output_tokens` from the done event's `usage` dict. Add extraction of `cache_read_input_tokens` and pass it to `self._token_usage.update()`.

## ALGORITHM — change in `stream_llm()`

```
# Existing:
input_tokens = usage.get("input_tokens", 0)
output_tokens = usage.get("output_tokens", 0)
# Add:
cache_read = usage.get("cache_read_input_tokens", 0)
# Update call:
self._token_usage.update(input_tokens, output_tokens, cache_read)  # was: (input_tokens, output_tokens)
```

That's it — 3 lines changed.

## HOW

- The `usage` dict in the "done" event already contains `cache_read_input_tokens` when emitted by Claude CLI (see `claude_code_cli_streaming.py:_map_stream_message_to_event`)
- LangChain will populate this in steps 4-5
- `cache_read_input_tokens` defaults to `0` via `.get()` so existing providers that don't emit it continue to work

## DATA

```python
# Done event with cache (from Claude CLI):
{"type": "done", "usage": {"input_tokens": 1200, "output_tokens": 800, "cache_read_input_tokens": 540}}

# Done event without cache (current LangChain):
{"type": "done", "usage": {"input_tokens": 100, "output_tokens": 50}}
# → cache_read defaults to 0, cache% hidden in display
```

## TESTS (`tests/icoder/test_app_core.py`)

Add these tests:

1. **`test_stream_llm_updates_cache_usage`** — FakeLLMService emits done event with `cache_read_input_tokens: 450` in usage dict. Verify `core.token_usage.last_cache_read == 450` and `core.token_usage.total_cache_read == 450`.

2. **`test_stream_llm_no_cache_in_usage`** — FakeLLMService emits done event with `usage: {"input_tokens": 100, "output_tokens": 50}` (no cache key). Verify `core.token_usage.last_cache_read == 0`.

3. **`test_stream_llm_cumulative_cache`** — Two stream calls, first with `cache_read_input_tokens: 200`, second with `cache_read_input_tokens: 300`. Verify `total_cache_read == 500`.

## COMMIT

```
feat(icoder): wire cache usage from done events through AppCore (#819)
```
