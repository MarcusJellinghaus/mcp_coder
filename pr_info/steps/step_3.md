# Step 3: Langchain — improved timeout messages (agent + text-stream)

> **Context**: See [summary.md](summary.md) for full issue context.

## Goal
Replace raw timeout messages in both langchain streaming paths with informative messages that include provider name, timeout value, what happened, and action hint.

## Files Modified

| File | Change |
|------|--------|
| `tests/llm/providers/langchain/test_langchain_streaming_timeout.py` | Update timeout message assertion |
| `tests/llm/providers/langchain/test_langchain_agent_timeout.py` | **New test**: agent inactivity timeout message assertion |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Improved messages in `_ask_agent_stream` and `_ask_text_stream` |

## Implementation Details

### 1. Tests first: `tests/llm/providers/langchain/test_langchain_streaming_timeout.py`

**Update** `test_text_stream_inactivity_timeout`:

Current assertion: `pytest.raises(TimeoutError, match="No LLM output for 1s")`

New match pattern:
```python
pytest.raises(
    TimeoutError,
    match=r"LLM inactivity timeout \(langchain\): no output for 1s\. Stream stalled\.",
)
```

The `test_text_stream_active_no_timeout` test is unchanged.

### 2. Tests: agent timeout

**No existing test covers the `_ask_agent_stream()` inactivity timeout.** Create a new test in the appropriate test file (e.g., `tests/llm/providers/langchain/test_langchain_agent_streaming.py` or a new file `tests/llm/providers/langchain/test_langchain_agent_timeout.py`).

The test should:
1. Mock the agent event queue to not produce any events (simulating timeout)
2. Verify `TimeoutError` is raised with the new message pattern: `r"LLM inactivity timeout \(langchain\): no response for \d+s\. Connection closed\."`

Read `_ask_agent_stream()` in `src/mcp_coder/llm/providers/langchain/__init__.py` (around line 490-500) to understand the `queue.Empty` → `TimeoutError` path and design the mock accordingly.

### 3. Source: `src/mcp_coder/llm/providers/langchain/__init__.py`

**Change A** — `_ask_agent_stream()` at line 499:

**Current**:
```python
raise TimeoutError(f"Agent produced no output for {timeout}s") from exc
```

**New**:
```python
raise TimeoutError(
    f"LLM inactivity timeout (langchain): no response for {timeout}s. "
    "Connection closed. You can retry, or use --timeout to increase the limit."
) from exc
```

**Change B** — `_ask_text_stream()` at line 608:

**Current**:
```python
raise TimeoutError(f"No LLM output for {timeout}s")
```

**New**:
```python
raise TimeoutError(
    f"LLM inactivity timeout (langchain): no output for {timeout}s. "
    "Stream stalled. You can retry, or use --timeout to increase the limit."
)
```

## LLM Prompt

```
Implement Step 3 from pr_info/steps/step_3.md.
Read pr_info/steps/summary.md for context.

This step improves timeout messages in both langchain streaming paths
(_ask_agent_stream and _ask_text_stream). Write tests first, then implement.
Run all checks after.
```
