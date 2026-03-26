# Step 4: LangChain Streaming Provider (Text-Only)

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 4: add `ask_langchain_stream()` with `_ask_text_stream()` to `src/mcp_coder/llm/providers/langchain/__init__.py`. Agent mode (when `mcp_config` is present) falls back to the existing blocking `ask_langchain()` and yields its result as stream events. Follow TDD — write tests first in `tests/llm/providers/langchain/test_langchain_provider.py`, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(langchain): add ask_langchain_stream`.

## WHERE

- **Modify**: `src/mcp_coder/llm/providers/langchain/__init__.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_provider.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_streaming.py` (streaming tests extracted to separate file)

## WHAT

### New functions in `__init__.py`:

```python
def ask_langchain_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> Iterator[StreamEvent]:
    """Stream LangChain responses as events.

    Same parameters as ask_langchain(). For text mode (no mcp_config),
    routes to _ask_text_stream() for real streaming. For agent mode
    (mcp_config present), falls back to blocking ask_langchain() and
    yields its result as text_delta + done events.

    Yields:
        StreamEvent dicts: text_delta, done, error, raw_line
    """


def _ask_text_stream(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
) -> Iterator[StreamEvent]:
    """Stream text-only responses using chat_model.stream().

    Yields:
        text_delta events for each chunk, then done event.
    """
```

## HOW

- Import `StreamEvent` from `mcp_coder.llm.types`
- Import `Iterator` from `collections.abc`
- **Text mode**: Replace `chat_model.invoke()` with `chat_model.stream()` — yields `AIMessageChunk` objects. Each chunk's `.content` becomes a `text_delta` event.
- **Agent mode (fallback)**: When `mcp_config` is present, call the existing blocking `ask_langchain()` and yield its text as a single `text_delta` event followed by a `done` event. This avoids async MCP tool complexity.
- **`raw_line` events**: For each yielded event, also serialize the native LangChain object as JSON and yield a `raw_line` event (for json-raw mode).
- **Session history**: Load/store using existing `load_langchain_history()` / `store_langchain_history()`
- **Error handling**: Catch provider errors via existing `_handle_provider_error()`, yield error event

## ALGORITHM

### _ask_text_stream:
```
history = load_langchain_history(session_id)
messages = messages_from_dict(history) + [HumanMessage(content=question)]
chat_model = _create_chat_model(config, timeout)
all_chunks = []
for chunk in chat_model.stream(messages):
    yield {"type": "raw_line", "line": json.dumps(chunk_to_dict(chunk))}
    yield {"type": "text_delta", "text": chunk.content}
    all_chunks.append(chunk)
store_langchain_history(session_id, serialize_messages(messages + [merge(all_chunks)]))
yield {"type": "done", "session_id": session_id, "usage": extract_usage(all_chunks)}
```

### Agent mode fallback (inside ask_langchain_stream):
```
if mcp_config:
    # Fall back to blocking ask_langchain() for agent mode
    response = ask_langchain(question, session_id, timeout, mcp_config, execution_dir, env_vars)
    yield {"type": "text_delta", "text": response.get("text", "")}
    yield {"type": "done", "session_id": response.get("session_id"), "usage": response.get("raw_response", {}).get("usage", {})}
    return
```

## DATA

### LangChain text stream → StreamEvent mapping

| LangChain object | StreamEvent |
|---|---|
| `AIMessageChunk(content="Hello")` | `{"type": "text_delta", "text": "Hello"}` |
| Final chunk (last) | `{"type": "done", "session_id": "...", "usage": {...}}` |

### Agent mode fallback → StreamEvent mapping

| Source | StreamEvent |
|---|---|
| `ask_langchain()` response text | `{"type": "text_delta", "text": "full response text"}` |
| After response | `{"type": "done", "session_id": "...", "usage": {...}}` |

## TEST CASES (write first)

1. `test_ask_langchain_stream_text_yields_deltas` — mock chat_model.stream() to yield chunks, verify text_delta events
2. `test_ask_langchain_stream_text_yields_raw_lines` — verify raw_line events for each chunk
3. `test_ask_langchain_stream_text_yields_done` — verify done event with session_id
4. `test_ask_langchain_stream_text_stores_history` — verify store_langchain_history called
5. `test_ask_langchain_stream_agent_falls_back_to_blocking` — mock ask_langchain(), verify it is called when mcp_config present, and result is yielded as text_delta + done events
6. `test_ask_langchain_stream_agent_fallback_yields_text` — verify text_delta contains full response text from blocking call
7. `test_ask_langchain_stream_routes_to_text_without_mcp_config` — verify no mcp_config routes to _ask_text_stream
8. `test_ask_langchain_stream_error_handling` — mock provider error, verify error event
