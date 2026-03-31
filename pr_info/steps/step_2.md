# Step 2: LangChain Text Stream Inactivity Timeout

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Add inactivity timeout tracking between chunks in `_ask_text_stream()` so that a
stalled LangChain model connection raises `TimeoutError` instead of hanging forever.

## WHERE

- **Modify:** `src/mcp_coder/llm/providers/langchain/__init__.py` — `_ask_text_stream()`
- **Create:** `tests/llm/providers/langchain/test_langchain_streaming_timeout.py`

## WHAT

### `_ask_text_stream()` — Add inactivity check in chunk loop

```python
# PSEUDOCODE — inside _ask_text_stream(), around the existing chunk loop
last_activity = time.time()
for chunk in chat_model.stream(lc_messages):
    if time.time() - last_activity > timeout:
        raise TimeoutError(f"No LLM output for {timeout}s")
    last_activity = time.time()
    # ... existing yield logic unchanged ...
```

**Note:** The timeout check happens *before* processing the chunk (catching gaps
between chunks). `time` is already imported in this module.

**Function signature unchanged:** `_ask_text_stream(question, config, backend, session_id, timeout) -> Iterator[StreamEvent]`

### `test_langchain_streaming_timeout.py` — New test file

Tests:

1. **`test_text_stream_inactivity_timeout`**: Mock `_create_chat_model` to return a
   fake model whose `.stream()` yields one chunk, then blocks (via `time.sleep()`).
   Call `_ask_text_stream()` with `timeout=1`. Assert `TimeoutError` is raised.

2. **`test_text_stream_active_no_timeout`**: Mock model that yields 3 chunks with
   no delay. Call with `timeout=2`. Assert all `text_delta` events received plus
   a `done` event. No error raised.

## HOW

- Use `unittest.mock.patch` to mock `_create_chat_model` in tests.
- Create a minimal fake chat model class with a `stream()` method that yields
  `MagicMock` objects with `.content` attribute and `.model_dump()` method.
- The test for timeout uses an iterator that yields one chunk, then sleeps.
- Import `_ask_text_stream` directly for unit testing (it's a module-level function).

## ALGORITHM

The check is 2 lines added to an existing loop — no separate algorithm needed.

## DATA

No new types. `TimeoutError` is a built-in exception. The existing `StreamEvent`
dict format is unchanged.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement step 2: Add inactivity timeout tracking between chunks in _ask_text_stream()
in src/mcp_coder/llm/providers/langchain/__init__.py. Write tests first in
tests/llm/providers/langchain/test_langchain_streaming_timeout.py, then implement.
Run all three MCP code quality checks after changes. Commit message: "icoder: langchain
text stream inactivity timeout"
```
