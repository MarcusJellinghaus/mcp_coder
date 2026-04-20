# Step 4: Reset busy indicator on stream end without `done` event (iCoder)

> **Context**: See [summary.md](summary.md) for full issue context.

## Goal

When the LLM stream ends with an error event (no `done`, no exception, no cancellation), the busy indicator stays stuck on "Querying LLM...". Fix by always resetting in the `finally` block.

## WHERE

- **Production**: `src/mcp_coder/icoder/ui/app.py` — `_stream_llm` method
- **Tests**: `tests/icoder/ui/test_app.py`

## WHAT

Expand the `finally` block in `_stream_llm` to always reset the busy indicator when neither exception nor cancellation already handled it.

**Current** `_stream_llm` finally block (lines ~174-178):

```python
finally:
    if self._cancel_event.is_set() and not _error_handled:
        self.call_from_thread(self._flush_buffer)
        self.call_from_thread(self._append_cancelled_marker)
        self.call_from_thread(self._reset_busy_indicator)
        self.call_from_thread(self._append_blank_line)
```

**New**:

```python
finally:
    if self._cancel_event.is_set() and not _error_handled:
        self.call_from_thread(self._flush_buffer)
        self.call_from_thread(self._append_cancelled_marker)
        self.call_from_thread(self._reset_busy_indicator)
        self.call_from_thread(self._append_blank_line)
    elif not _error_handled:
        self.call_from_thread(self._reset_busy_indicator)
```

## HOW

- `show_ready()` (called by `_reset_busy_indicator`) is idempotent — calling it after `done` already triggered it via `_handle_stream_event` → `StreamDone` → `show_ready()` is harmless
- The `_error_handled` flag prevents double-reset when exception handler already called it
- Cancellation path already resets — the `elif` avoids double-reset there too
- No new imports needed

## ALGORITHM

```
1. try: iterate stream events
2. except: set _error_handled, flush, show error, reset indicator
3. finally:
4.   if cancelled and not error_handled → flush, cancel marker, reset (existing)
5.   elif not error_handled → reset indicator (NEW)
6. show_ready() is idempotent, so redundant calls are safe
```

## DATA

- No data changes. Pure UI state management.

## Tests

Add to `tests/icoder/ui/test_app.py`:

- **`test_busy_indicator_resets_on_error_only_stream`** — create app with `FakeLLMService` that yields only an error event (no `done`), submit input, verify `BusyIndicator` shows ready state after stream completes. Use `async with app.run_test()` pattern matching existing tests.

## LLM Prompt

```
Implement Step 4 from pr_info/steps/step_4.md.
Read pr_info/steps/summary.md for full context.

Fix the `_stream_llm` finally block in `src/mcp_coder/icoder/ui/app.py` to always reset
the busy indicator. Add test in `tests/icoder/ui/test_app.py`.
Run all three code quality checks after changes.
```
