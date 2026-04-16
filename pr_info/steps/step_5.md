# Step 5: LangChain agent paths — sum usage across steps

> **Context**: See `pr_info/steps/summary.md` for full issue context. This is step 5 of 5.

## LLM Prompt

```
Implement step 5 of issue #819 (pr_info/steps/summary.md).
Sum token usage across all LLM calls in run_agent() and run_agent_stream().
Import _extract_usage and _sum_usage from mcp_coder.llm.providers.langchain._usage
(created in step 4). Write tests first (TDD), then implement. Run all three checks after.
```

## WHERE

- **Modify**: `src/mcp_coder/llm/providers/langchain/agent.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_agent.py`
- **Modify**: `tests/llm/providers/langchain/test_langchain_agent_streaming.py`

## WHAT

### `run_agent()` change

In the existing loop that iterates `output_messages` to count tool calls (lines 309-320), also extract and sum `usage_metadata` from each `AIMessage`. Add result to `stats`:
```python
stats["usage"] = accumulated_usage
```

### `run_agent_stream()` change

Listen for `on_chat_model_end` events (which carry the full `AIMessage` with `usage_metadata`). Sum usage across all such events. Include in the final "done" event:
```python
yield {"type": "done", "session_id": session_id, "usage": accumulated_usage}
```

## HOW — imports

```python
from mcp_coder.llm.providers.langchain._usage import _extract_usage, _sum_usage
```

These helpers live in the dedicated `_usage.py` submodule (step 4) to avoid circular-import risk between `langchain/__init__.py` and `agent.py`.

## ALGORITHM — `run_agent()` addition

```python
# Inside existing AIMessage loop:
accumulated_usage: UsageInfo = {}
for msg in output_messages:
    if isinstance(msg, AIMessage):
        msg_usage = _extract_usage(msg)
        if msg_usage:
            accumulated_usage = _sum_usage(accumulated_usage, msg_usage)
# ...
stats["usage"] = accumulated_usage
```

## ALGORITHM — `run_agent_stream()` addition

```python
accumulated_usage: UsageInfo = {}

# Inside the event loop, add a new elif branch:
elif event_kind == "on_chat_model_end":
    output_msg = event.get("data", {}).get("output")
    if output_msg is not None:
        msg_usage = _extract_usage(output_msg)
        if msg_usage:
            accumulated_usage = _sum_usage(accumulated_usage, msg_usage)

# In final done event (replace existing line):
yield {"type": "done", "session_id": session_id, "usage": accumulated_usage}
```

## DATA

Agent with 2 LLM calls:
```python
# Call 1: AIMessage with usage_metadata = {input_tokens: 500, output_tokens: 200, ...cache_read: 100}
# Call 2: AIMessage with usage_metadata = {input_tokens: 800, output_tokens: 300, ...cache_read: 200}
# → accumulated: {input_tokens: 1300, output_tokens: 500, cache_read_input_tokens: 300}
```

## TESTS

### `tests/llm/providers/langchain/test_langchain_agent.py`

1. **`test_run_agent_stats_include_usage`** — mock `agent.ainvoke()` returning messages where `AIMessage`s have `usage_metadata`. Tests MUST construct real `langchain_core.messages.AIMessage(content=..., usage_metadata={...})` instances (NOT `Mock` objects) to mirror actual attribute access in the production code path. Verify `stats["usage"]` contains summed values.

2. **`test_run_agent_stats_usage_empty_when_no_metadata`** — mock `AIMessage`s without `usage_metadata`. Verify `stats["usage"]` is empty dict `{}`.

3. **`test_run_agent_stats_usage_sums_multiple_steps`** — mock two `AIMessage`s with different `usage_metadata` values. Verify `stats["usage"]` is the sum.

### `tests/llm/providers/langchain/test_langchain_agent_streaming.py`

4. **`test_agent_stream_done_event_includes_usage`** — mock `astream_events` with `on_chat_model_end` events containing `AIMessage` with `usage_metadata`. Verify the "done" event has `usage` dict.

5. **`test_agent_stream_done_event_sums_usage`** — two `on_chat_model_end` events with different usage. Verify done event `usage` is the sum.

6. **`test_agent_stream_done_event_no_usage`** — no `on_chat_model_end` events (or no `usage_metadata`). Verify done event has empty `usage` dict.

## COMMIT

```
feat(langchain): sum token usage across agent steps (#819)
```
