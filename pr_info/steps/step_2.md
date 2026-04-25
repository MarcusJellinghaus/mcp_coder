# Step 2 — Enhance iCoder event log with stream events

> See [summary.md](summary.md) for full context on issue #897.

## Goal

Log each stream event (except `raw_line`) to the iCoder JSONL event log for
debugging and future replay-based testing.

## WHERE

- **Source:** `src/mcp_coder/icoder/core/app_core.py` — `stream_llm()` method, line ~91-107
- **Tests:** `tests/icoder/test_app_core.py`

## WHAT

One line added inside the existing `for event in self._llm_service.stream(text):` loop.

## HOW

After `assembler.add(event)` and before the existing `if event.get("type") == "done":` block,
add:

```python
if event.get("type") != "raw_line":
    self._event_log.emit("stream_event", **event)
```

No new imports, no config flags, no changes to `EventLog` class.

## ALGORITHM

```
for event in self._llm_service.stream(text):
    assembler.add(event)
    if event.get("type") != "raw_line":        # ← NEW
        self._event_log.emit("stream_event", **event)  # ← NEW
    if event.get("type") == "done":
        # existing usage extraction...
    yield event
```

## DATA

Each emitted event log entry has:
- `event`: `"stream_event"` (fixed string)
- `**event`: all fields from the StreamEvent dict (`type`, `text`, `name`, `output`, etc.)

The JSONL line looks like: `{"t": 1.23, "event": "stream_event", "type": "text_delta", "text": "hello"}`

## Tests (TDD — write first)

Add to `tests/icoder/test_app_core.py`:

1. **`test_stream_events_logged`** — Create a `FakeLLMService` with a custom event list
   containing `text_delta`, `tool_use_start`, `tool_result`, and `done` events. Build an
   `AppCore` from it. Call `stream_llm()`. Assert `event_log.entries` contains entries with
   `event == "stream_event"`. Verify that multiple event types (`text_delta`, `tool_use_start`,
   `tool_result`, `done`) appear in the logged data.

2. **`test_raw_line_events_not_logged`** — Create a `FakeLLMService` with a custom event list
   that includes both a `{"type": "raw_line", ...}` event and a `{"type": "text_delta", ...}`
   event. Build an `AppCore` from it. Call `stream_llm()`. Assert that `text_delta` appears
   in the logged `stream_event` entries but `raw_line` does not.

Both tests create their own `FakeLLMService(responses=...)` with custom event lists
and build an `AppCore` from it, following the pattern in `test_stream_llm_updates_token_usage`.
They use the `event_log` fixture from conftest.

## Commit

```
feat: log stream events to iCoder JSONL event log (#897)

Emit stream events (excluding raw_line) to EventLog for debugging
and future replay-based testing.
```
