# Step 2: Wire `BusyIndicator` into `app.py`

> See [summary.md](summary.md) for full context and architectural decisions.

## LLM Prompt

Wire the `BusyIndicator` widget into iCoder's `app.py` (issue #752). Read `pr_info/steps/summary.md` for context, then implement this step. The widget was created in step 1. Now add it to the layout and connect it to stream events. Write tests first, then implementation.

## WHERE

- **Modify**: `src/mcp_coder/icoder/ui/app.py`
- **Modify**: `tests/icoder/test_app_pilot.py` — add integration tests

## WHAT

### Changes to `ICoderApp`

| Method | Change |
|--------|--------|
| `compose()` | Add `yield BusyIndicator()` between `CommandAutocomplete` and `InputArea` |
| `_handle_stream_event()` | Call `show_busy`/`show_ready` on indicator based on event type |
| `_stream_llm()` | Reset indicator to ready in the `except` block |

### Event-to-indicator mapping

```python
# In _handle_stream_event:
if isinstance(action, TextChunk):
    self.query_one(BusyIndicator).show_busy("Thinking...")
    # ... existing buffer logic ...

elif isinstance(action, ToolStart):
    self.query_one(BusyIndicator).show_busy(action.display_name)
    # ... existing tool rendering ...

elif isinstance(action, StreamDone):
    self.query_one(BusyIndicator).show_ready()
    # ... existing blank line ...
```

```python
# In _stream_llm except block, add:
self.call_from_thread(self._reset_busy_indicator)
```

### New private helper

```python
def _reset_busy_indicator(self) -> None:
    self.query_one(BusyIndicator).show_ready()
```

## HOW

- Import `BusyIndicator` from `mcp_coder.icoder.ui.widgets.busy_indicator`
- Insert in `compose()` between `CommandAutocomplete` and `InputArea`
- Add indicator calls at the start of existing `isinstance` branches (before existing logic)
- Add `_reset_busy_indicator` call in the error path of `_stream_llm`

## ALGORITHM

```
_handle_stream_event(event):
    action = renderer.render(event)
    if TextChunk:   indicator.show_busy("Thinking...")
    if ToolStart:   indicator.show_busy(action.display_name)
    if StreamDone:  indicator.show_ready()
    ... existing rendering logic unchanged ...

_stream_llm(text):
    try: stream events
    except:
        flush_buffer()
        show_error()
        reset_busy_indicator()    ← NEW
        append_blank_line()
```

## DATA

No new data structures. Uses existing `BusyIndicator` API from step 1.

## TESTS (additions to `tests/icoder/test_app_pilot.py`)

1. **`test_busy_indicator_shows_ready_on_startup`** — After mount, `BusyIndicator` renderable contains `✓ Ready`
2. **`test_busy_indicator_shows_ready_after_streaming`** — After a full stream (text + done), indicator is back to `✓ Ready`
3. **`test_busy_indicator_shows_tool_name_during_tool_use`** — Directly call `_handle_stream_event` with `tool_use_start`, verify indicator shows tool display name
4. **`test_busy_indicator_resets_on_stream_error`** — Use `ErrorAfterChunksLLMService`, verify indicator returns to `✓ Ready` after error

## Commit

```
feat(icoder): wire BusyIndicator into app layout and stream events (#752)
```
