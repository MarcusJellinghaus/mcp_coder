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

1. **`test_stream_events_logged`** — Use `FakeLLMService` with canned response containing
   `text_delta` and `done` events. Call `stream_llm()`. Assert `event_log.entries` contains
   entries with `event == "stream_event"`. Verify both `text_delta` and `done` types appear
   in the logged data.

2. **`test_raw_line_events_not_logged`** — Use `FakeLLMService` with a response that includes
   a `{"type": "raw_line", ...}` event. Call `stream_llm()`. Assert no `stream_event` entry
   has `data["type"] == "raw_line"`.

Both tests use the existing `app_core` / `event_log` fixtures from `conftest.py`.
The `FakeLLMService` accepts custom response lists via `responses=` parameter.

## Commit

```
feat: log stream events to iCoder JSONL event log (#897)

Emit stream events (excluding raw_line) to EventLog for debugging
and future replay-based testing.
```
