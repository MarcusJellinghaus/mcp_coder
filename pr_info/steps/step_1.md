# Step 1: Stream Event Types and ResponseAssembler

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 1: add `StreamEvent` type alias and `ResponseAssembler` class to the existing `src/mcp_coder/llm/types.py`. Follow TDD — write tests first in `tests/llm/test_types.py`, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(types): add StreamEvent type and ResponseAssembler`.

## WHERE

- **Modify**: `src/mcp_coder/llm/types.py`
- **Modify**: `tests/llm/test_types.py`

## WHAT

### In `src/mcp_coder/llm/types.py`:

```python
# Type alias for stream events — plain dicts with a "type" key
StreamEvent = dict[str, object]
"""Stream event dict. Always has a "type" key. Known types:

- {"type": "text_delta", "text": "..."} — incremental text token
- {"type": "tool_use_start", "name": "...", "args": {...}} — tool call begins
- {"type": "tool_result", "name": "...", "output": "..."} — tool call result
- {"type": "error", "message": "..."} — error during stream
- {"type": "done", "usage": {...}} — stream complete with optional usage stats
- {"type": "raw_line", "line": "..."} — raw NDJSON line passthrough (json-raw mode)
"""


class ResponseAssembler:
    """Accumulates StreamEvents into a complete LLMResponseDict."""

    def __init__(self, provider: str) -> None: ...
    def add(self, event: StreamEvent) -> None: ...
    def result(self) -> LLMResponseDict: ...
```

### Function signatures:

```python
def __init__(self, provider: str) -> None:
    """Initialize assembler for given provider name."""

def add(self, event: StreamEvent) -> None:
    """Process a single stream event, accumulating text and metadata."""

def result(self) -> LLMResponseDict:
    """Build and return the final LLMResponseDict from accumulated events."""
```

## HOW

- Add to existing `__all__` list: `"StreamEvent"`, `"ResponseAssembler"`
- Add `from datetime import datetime` import
- `ResponseAssembler` uses `datetime.now().isoformat()` for timestamp (import `datetime`)

## ALGORITHM

```
class ResponseAssembler:
    init(provider):
        text_parts = [], session_id = None, usage = {}, raw_events = [], error = None

    add(event):
        raw_events.append(event)
        if event.type == "text_delta": text_parts.append(event.text)
        if event.type == "done": usage = event.usage; session_id = event.session_id
        if event.type == "error": error = event.message

    result() -> LLMResponseDict:
        return {version, timestamp, text=join(text_parts), session_id, provider, raw_response={events, usage, error}}
```

## DATA

### Input: `StreamEvent` examples

```python
{"type": "text_delta", "text": "Hello"}
{"type": "tool_use_start", "name": "sleep", "args": {"seconds": 2}}
{"type": "tool_result", "name": "sleep", "output": "done"}
{"type": "done", "usage": {"input_tokens": 100, "output_tokens": 50}, "session_id": "abc123"}
{"type": "error", "message": "Connection reset"}
```

### Output: `LLMResponseDict`

```python
{
    "version": "1.0",
    "timestamp": "2026-03-26T10:00:00.000000",
    "text": "Hello world",
    "session_id": "abc123",
    "provider": "claude",
    "raw_response": {
        "events": [...],
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }
}
```

## TEST CASES (write first)

1. `test_stream_event_type_alias` — verify `StreamEvent` is `dict[str, object]`
2. `test_response_assembler_text_delta` — feed text_delta events, verify assembled text
3. `test_response_assembler_done_event` — feed done event with usage/session_id, verify result
4. `test_response_assembler_error_event` — feed error event, verify error in raw_response
5. `test_response_assembler_tool_events` — feed tool_use_start + tool_result, verify in raw_response events
6. `test_response_assembler_empty` — no events, result has empty text and None session_id
7. `test_response_assembler_provider` — verify provider field matches constructor arg
