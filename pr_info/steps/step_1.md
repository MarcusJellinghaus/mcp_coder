# Step 1: Cancel infrastructure + Escape binding + cancel logic

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: Add the `STYLE_CANCELLED` constant, `_cancel_event` threading.Event to `ICoderApp.__init__`, the Escape key binding, `action_cancel_stream()`, and modify `_stream_llm()` to check the cancel event between iterations. On cancel: flush buffer, append "— Cancelled —" marker, reset busy indicator. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- `src/mcp_coder/icoder/ui/app.py` — constant, `__init__` change, bindings, action method, `_stream_llm()` modification
- `tests/icoder/test_app_pilot.py` — cancel tests

## WHAT

### Constants

```python
STYLE_CANCELLED = "dim #e8a838"  # dim orange — visible but not alarming
```

Add near existing `STYLE_USER_INPUT` and `STYLE_TOOL_OUTPUT` constants.

### `ICoderApp.__init__` change

```python
import threading

def __init__(self, app_core: AppCore, *, format_tools: bool = True, **kwargs):
    ...
    self._cancel_event = threading.Event()
```

### Bindings

```python
from textual.binding import Binding

class ICoderApp(App[None]):
    BINDINGS = [
        Binding("escape", "cancel_stream", "Cancel", show=False),
    ]
```

### `action_cancel_stream()`

```python
def action_cancel_stream(self) -> None:
    """Set cancel event if currently streaming. No-op otherwise."""
    self._cancel_event.set()
```

### `_stream_llm()` modification

```python
def _stream_llm(self, text: str) -> None:
    self._cancel_event.clear()
    try:
        for event in self._core.stream_llm(text):
            if self._cancel_event.is_set():
                break
            self.call_from_thread(self._handle_stream_event, event)
    except Exception as exc:
        ...  # existing error handling unchanged
    finally:
        if self._cancel_event.is_set():
            self.call_from_thread(self._flush_buffer)
            self.call_from_thread(
                self._append_cancelled_marker
            )
            self.call_from_thread(self._reset_busy_indicator)
            self.call_from_thread(self._append_blank_line)
```

### `_append_cancelled_marker()`

```python
def _append_cancelled_marker(self) -> None:
    """Append dim orange '— Cancelled —' marker to output."""
    self.query_one(OutputLog).append_text("— Cancelled —", style=STYLE_CANCELLED)
```

## ALGORITHM (cancel flow)

```
1. User presses Escape → action_cancel_stream() sets _cancel_event
2. _stream_llm() checks _cancel_event.is_set() at top of loop iteration
3. If set: break out of for-loop (triggers GeneratorExit down the chain)
4. finally block detects cancellation: flush buffer, append marker, reset busy
5. _cancel_event.clear() at start of next _stream_llm() call resets state
```

## HOW

- `import threading` at top of `app.py`
- Add `STYLE_CANCELLED` constant after existing style constants
- Add `self._cancel_event = threading.Event()` in `__init__` after `self._text_buffer`
- Add `from textual.binding import Binding` import
- Add `BINDINGS` class variable to `ICoderApp`
- Add `action_cancel_stream()` method
- Modify `_stream_llm()`: add `self._cancel_event.clear()` at start, add `if self._cancel_event.is_set(): break` in loop, add cancel handling in finally
- Add `_append_cancelled_marker()` method

## TESTS

### Test: Escape during streaming cancels and shows marker

```python
async def test_escape_cancels_streaming(make_icoder_app):
    """Escape during streaming breaks the loop and shows cancelled marker."""
    import time
    from collections.abc import Iterator

    class SlowLLMService:
        """LLM service that yields events with delays to simulate streaming."""

        def stream(self, question: str) -> Iterator[StreamEvent]:
            for i in range(20):
                time.sleep(0.05)
                yield {"type": "text_delta", "text": f"chunk{i} "}
            yield {"type": "done"}

        @property
        def provider(self) -> str:
            return "claude"

        @property
        def session_id(self) -> str | None:
            return None

        def reset_session(self) -> None:
            pass

    app = make_icoder_app(llm_service=SlowLLMService())
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        output = app.query_one(OutputLog)
        assert "— Cancelled —" in output.recorded_lines
```

### Test: Escape when idle is a no-op

```python
async def test_escape_when_idle_is_noop(icoder_app):
    """Escape when not streaming does nothing harmful."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert "— Cancelled —" not in output.recorded_lines
```

### Test: Busy indicator resets after cancel

```python
async def test_busy_indicator_resets_after_cancel(make_icoder_app):
    """After Escape cancel, busy indicator shows '✓ Ready'."""
    import time
    from collections.abc import Iterator

    class SlowLLMService:
        def stream(self, question: str) -> Iterator[StreamEvent]:
            for i in range(20):
                time.sleep(0.05)
                yield {"type": "text_delta", "text": f"chunk{i} "}
            yield {"type": "done"}

        @property
        def provider(self) -> str:
            return "claude"

        @property
        def session_id(self) -> str | None:
            return None

        def reset_session(self) -> None:
            pass

    app = make_icoder_app(llm_service=SlowLLMService())
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        indicator = app.query_one(BusyIndicator)
        assert "✓ Ready" in indicator.label_text
```

### Test: Session preserved after cancel (no reset)

```python
async def test_session_preserved_after_cancel(make_icoder_app):
    """Cancel doesn't reset session — previous session ID persists."""
    import time
    from collections.abc import Iterator

    class SlowLLMServiceWithSession:
        def __init__(self):
            self._session_id = "test-session-123"

        def stream(self, question: str) -> Iterator[StreamEvent]:
            for i in range(20):
                time.sleep(0.05)
                yield {"type": "text_delta", "text": f"chunk{i} "}
            yield {"type": "done"}

        @property
        def provider(self) -> str:
            return "claude"

        @property
        def session_id(self) -> str | None:
            return self._session_id

        def reset_session(self) -> None:
            self._session_id = None

    svc = SlowLLMServiceWithSession()
    app = make_icoder_app(llm_service=svc)
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        # Session should NOT have been reset by cancel
        assert svc.session_id == "test-session-123"
```

## DATA

- `STYLE_CANCELLED`: `str` — Rich style string for dim orange text
- `_cancel_event`: `threading.Event` — initially unset
- `action_cancel_stream()` → `None` (side effect: sets `_cancel_event`)
- `_append_cancelled_marker()` → `None` (side effect: appends styled text to OutputLog)
- Cancel marker text: `"— Cancelled —"` with style `STYLE_CANCELLED`
