# Step 2: Add `run_agent_stream()` Async Generator

**Commit message:** `feat(agent): add run_agent_stream async generator with astream_events`

**References:** [summary.md](summary.md) — "Async-to-Sync Bridge" section, `run_agent_stream()` box

## LLM Prompt

> Implement Step 2 from `pr_info/steps/step_2.md`.
> Read `pr_info/steps/summary.md` for full context (issue #603).
> Read the existing code in `src/mcp_coder/llm/providers/langchain/agent.py` and
> `tests/llm/providers/langchain/test_langchain_streaming.py` before making changes.
> Also read `tests/llm/providers/langchain/conftest.py` to understand mock setup.
> Follow TDD: write tests first, then implement, then run all three checks.

## WHERE

- `tests/llm/providers/langchain/test_langchain_streaming.py` — add test class
- `src/mcp_coder/llm/providers/langchain/agent.py` — add `run_agent_stream()`

## WHAT — Tests First

Add `TestRunAgentStream` class to `test_langchain_streaming.py`:

```python
class TestRunAgentStream:
    """Tests for run_agent_stream() async generator event mapping."""

    @pytest.mark.asyncio
    async def test_text_delta_from_chat_model_stream(self) -> None:
        """on_chat_model_stream events become text_delta StreamEvents."""
        # Mock agent with astream_events yielding on_chat_model_stream
        # Verify text_delta events with correct text extraction

    @pytest.mark.asyncio
    async def test_text_delta_list_content_format(self) -> None:
        """AIMessageChunk with list-of-blocks content is handled."""
        # Content: [{"type": "text", "text": "Hello"}]
        # Verify text extracted correctly

    @pytest.mark.asyncio
    async def test_tool_use_start_from_on_tool_start(self) -> None:
        """on_tool_start events become tool_use_start StreamEvents."""
        # Verify name, args (serialized JSON), tool_call_id

    @pytest.mark.asyncio
    async def test_tool_result_from_on_tool_end(self) -> None:
        """on_tool_end events become tool_result StreamEvents."""
        # Verify name, output, tool_call_id

    @pytest.mark.asyncio
    async def test_raw_line_emitted_for_every_event(self) -> None:
        """Every astream_events dict is also emitted as raw_line."""

    @pytest.mark.asyncio
    async def test_done_event_emitted_last(self) -> None:
        """Stream ends with done event containing session_id."""

    @pytest.mark.asyncio
    async def test_history_stored_before_done(self) -> None:
        """store_langchain_history called before done event is yielded."""

    @pytest.mark.asyncio
    async def test_error_propagation(self) -> None:
        """Errors from astream_events propagate as error event + exception."""
```

**Note:** These tests mock `MultiServerMCPClient`, `create_react_agent`, and `astream_events`.
Use `conftest.py`'s existing mock setup for langchain imports. Add `pytest-asyncio` marker.

Tests mock the entire `astream_events` output including `AIMessageChunk`-like objects (plain dicts or
simple mock objects with `.content` attribute). No changes to `conftest.py` are needed since we mock
at the `astream_events` level, not at the message class level.

These are unit tests — do NOT add `langchain_integration` marker. They will run in the default test suite.

## WHAT — Implementation

Add to `src/mcp_coder/llm/providers/langchain/agent.py`:

```python
async def run_agent_stream(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    session_id: str,
    cancel_event: threading.Event | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> AsyncIterator[StreamEvent]:
```

**New import at top of agent.py:**
```python
import threading
from collections.abc import AsyncIterator
from mcp_coder.llm.types import StreamEvent
```

## ALGORITHM

```python
async def run_agent_stream(...) -> AsyncIterator[StreamEvent]:
    # 1. Load MCP tools (inline, same as run_agent)
    # 2. Create agent via create_react_agent(chat_model, all_tools)
    # 3. Build input_messages from history + question
    # 4. async for event in agent.astream_events(input, version="v2"):
    #      if cancel_event and cancel_event.is_set(): break
    #      yield raw_line event (JSON-serialized event dict)
    #      map event to StreamEvent via if/elif on event["event"]
    # 5. Store history via store_langchain_history()
    # 6. yield done event with session_id
```

**Note on tool_call_id:** LangChain's `astream_events` v2 does not include `tool_call_id` in `on_tool_start` events. We use `run_id` (unique per tool invocation) as the correlation key in `tool_use_start`. For `tool_result`, we extract the real `tool_call_id` from the `ToolMessage` output when available, falling back to `run_id`. Both `on_tool_start` and `on_tool_end` share the same `run_id`, so consumers can correlate starts with results using either field.

## Event Mapping (if/elif chain)

```python
event_kind = event["event"]

if event_kind == "on_chat_model_stream":
    chunk = event["data"].get("chunk")
    content = chunk.content if chunk else ""
    # Handle string content
    if isinstance(content, str) and content:
        yield {"type": "text_delta", "text": content}
    # Handle list-of-blocks content (Anthropic)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    yield {"type": "text_delta", "text": text}

elif event_kind == "on_tool_start":
    metadata = event.get("metadata", {})  # or event["data"]
    yield {
        "type": "tool_use_start",
        "name": event.get("name", ""),
        "args": json.dumps(event["data"].get("input", {})),
        "tool_call_id": event.get("run_id", ""),  # run_id for start/end correlation
    }

elif event_kind == "on_tool_end":
    output = event["data"].get("output", "")
    # ToolMessage has the real tool_call_id from the LLM
    tool_call_id = getattr(output, "tool_call_id", None) or event.get("run_id", "")
    yield {
        "type": "tool_result",
        "name": event.get("name", ""),
        "output": str(output),
        "tool_call_id": tool_call_id,
    }
```

## HISTORY ACCUMULATION

Since `astream_events()` yields individual events (not full message objects like `ainvoke()`),
we must reconstruct the conversation for history storage:

1. Before streaming: build `input_messages` from history + new `HumanMessage(question)`
2. During streaming: accumulate text from `text_delta` events into a buffer string
3. During streaming: accumulate tool calls from `on_tool_start`/`on_tool_end` into a list
4. After streaming completes: construct `AIMessage(content=accumulated_text, tool_calls=accumulated_tool_calls)`
   and any `ToolMessage` objects from tool results
5. Serialize all messages via `message_to_dict()` and pass to `store_langchain_history()`

This keeps history storage self-contained within `run_agent_stream()` without extra API calls.

## DATA

- **Input**: Same as `run_agent()` plus `session_id: str` and `cancel_event: threading.Event | None`
- **Yields**: `StreamEvent` dicts (`text_delta`, `tool_use_start`, `tool_result`, `raw_line`, `done`)
- **Side effect**: Calls `store_langchain_history()` before yielding `done`

## HOW — Integration

- Import `threading` and `AsyncIterator` at module top
- Import `StreamEvent` from `mcp_coder.llm.types`
- Import `json` (already imported)
- Import `store_langchain_history` from `mcp_coder.llm.storage.session_storage` (deferred inside function)
- `cancel_event` parameter allows Step 4's bridge to signal cancellation

## Verification

Run all three checks after implementation:
1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
3. `mcp__tools-py__run_mypy_check`
