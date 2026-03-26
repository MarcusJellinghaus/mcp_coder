# Step 4: LangChain Streaming Provider

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 4: add `ask_langchain_stream()` with `_ask_text_stream()` and `_ask_agent_stream()` to `src/mcp_coder/llm/providers/langchain/__init__.py`. Follow TDD — write tests first in `tests/llm/providers/langchain/test_langchain_provider.py`, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(langchain): add ask_langchain_stream`.

## WHERE

- **Modify**: `src/mcp_coder/llm/providers/langchain/__init__.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_provider.py`

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

    Same parameters as ask_langchain(). Routes to _ask_text_stream()
    or _ask_agent_stream() based on mcp_config presence.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error, raw_line
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


def _ask_agent_stream(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None,
    env_vars: dict[str, str] | None,
    timeout: int,
) -> Iterator[StreamEvent]:
    """Stream agent responses using agent.stream() (sync).

    Yields:
        text_delta, tool_use_start, tool_result events, then done event.
    """
```

## HOW

- Import `StreamEvent` from `mcp_coder.llm.types`
- Import `Iterator` from `collections.abc`
- **Text mode**: Replace `chat_model.invoke()` with `chat_model.stream()` — yields `AIMessageChunk` objects. Each chunk's `.content` becomes a `text_delta` event.
- **Agent mode**: Use sync `agent.stream()` from langgraph — yields dicts with agent steps. Map to `tool_use_start`, `tool_result`, and `text_delta` events.
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

### _ask_agent_stream:
```
agent = create_react_agent(chat_model, tools)
input_messages = history + [HumanMessage(content=question)]
for step in agent.stream({"messages": input_messages}):
    yield {"type": "raw_line", "line": json.dumps(step, default=str)}
    for event in map_agent_step_to_events(step):
        yield event
# After stream completes:
store_langchain_history(session_id, serialize_output_messages(step))
yield {"type": "done", "session_id": session_id, "usage": {}}
```

## DATA

### LangChain text stream → StreamEvent mapping

| LangChain object | StreamEvent |
|---|---|
| `AIMessageChunk(content="Hello")` | `{"type": "text_delta", "text": "Hello"}` |
| Final chunk (last) | `{"type": "done", "session_id": "...", "usage": {...}}` |

### LangChain agent stream → StreamEvent mapping

| Agent step dict key | StreamEvent |
|---|---|
| `{"agent": {"messages": [AIMessage(tool_calls=[...])]}}` | `{"type": "tool_use_start", "name": "...", "args": {...}}` |
| `{"tools": {"messages": [ToolMessage(content="...")]}}` | `{"type": "tool_result", "name": "...", "output": "..."}` |
| `{"agent": {"messages": [AIMessage(content="final text")]}}` | `{"type": "text_delta", "text": "final text"}` |

## TEST CASES (write first)

1. `test_ask_langchain_stream_text_yields_deltas` — mock chat_model.stream() to yield chunks, verify text_delta events
2. `test_ask_langchain_stream_text_yields_raw_lines` — verify raw_line events for each chunk
3. `test_ask_langchain_stream_text_yields_done` — verify done event with session_id
4. `test_ask_langchain_stream_text_stores_history` — verify store_langchain_history called
5. `test_ask_langchain_stream_agent_yields_tool_events` — mock agent.stream(), verify tool_use_start and tool_result events
6. `test_ask_langchain_stream_agent_yields_text` — verify text_delta from final agent response
7. `test_ask_langchain_stream_routes_to_agent` — verify mcp_config triggers agent mode
8. `test_ask_langchain_stream_error_handling` — mock provider error, verify error event
