# Step 7: UI Layer + Pilot Integration Tests

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Steps 1-6 (all core, services, CLI)

## Goal
Implement the Textual UI shell: `ICoderApp`, `OutputLog`, `InputArea`, and CSS styles. Wire UI events to `AppCore`. Add Textual pilot integration tests using headless mode.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/ui/app.py`
- `src/mcp_coder/icoder/ui/styles.py`
- `src/mcp_coder/icoder/ui/widgets/output_log.py`
- `src/mcp_coder/icoder/ui/widgets/input_area.py`
- `tests/icoder/test_app_pilot.py`

## WHAT — Main Functions and Signatures

### `ui/styles.py`

```python
CSS: str = """
/* Vertical layout: output on top, input at bottom */
/* RichLog takes most space, TextArea is fixed height */
"""
```

### `ui/widgets/output_log.py`

```python
class OutputLog(RichLog):
    """Scrollable output area for conversation display."""
    # Thin wrapper — may add helper methods for writing structured output
    
    def append_text(self, text: str) -> None:
        """Write text to the output log."""

    def append_tool_use(self, name: str, args: str, result: str) -> None:
        """Write compact tool use line: ⚙ name(args) → result"""
```

### `ui/widgets/input_area.py`

```python
class InputArea(TextArea):
    """Text input with Enter=submit, Shift-Enter=newline.
    
    Posts InputSubmitted message when Enter is pressed.
    """

    class InputSubmitted(Message):
        """Posted when user presses Enter to submit input."""
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()
```

### `ui/app.py`

```python
class ICoderApp(App):
    """Interactive coding TUI. Thin shell over AppCore."""

    def __init__(self, app_core: AppCore) -> None: ...

    def compose(self) -> ComposeResult:
        """Vertical layout: OutputLog on top, InputArea at bottom."""

    def on_mount(self) -> None:
        """Focus input area on startup."""

    def on_input_area_input_submitted(self, message: InputArea.InputSubmitted) -> None:
        """Handle submitted input: route through AppCore."""

    def _stream_llm(self, text: str) -> None:
        """Worker target: stream LLM response in background thread.
        
        Called via run_worker(thread=True). Uses call_from_thread()
        to post incremental updates to the UI event loop.
        """
```

## HOW — Integration Points

- `ICoderApp` receives `AppCore` via constructor injection
- `compose()` returns `OutputLog()` + `InputArea()` in a vertical layout
- `on_input_area_input_submitted()`:
  1. Show user input in output log (echo)
  2. Call `app_core.handle_input(text)`
  3. If `response.text` → append to output
  4. If `response.clear_output` → clear output log
  5. If `response.quit` → `self.exit()`
  6. If `response.send_to_llm` → `self.run_worker(self._stream_llm, text, thread=True)`
  7. Clear input area
- `_stream_llm()` runs in worker thread:
  1. Iterates `app_core.stream_llm(text)`
  2. For each `StreamEvent`, calls `self.call_from_thread(self._handle_stream_event, event)`
  3. `_handle_stream_event()` updates `OutputLog` based on event type
- MCP tool display: `text_delta` → append text, `tool_use_start` → `⚙ name(args)...`, `tool_result` → `→ done`, `error` → display error text
- CSS: `OutputLog` gets `height: 1fr`, `InputArea` gets `height: auto` with max ~5 lines

### Key Textual patterns
- `InputArea` overrides `_on_key()` to intercept Enter vs Shift-Enter
- `InputSubmitted` is a Textual `Message` — auto-dispatched to parent via naming convention
- Worker errors caught and displayed in output area (app stays alive)

## ALGORITHM — Core Logic

```
on_input_area_input_submitted(message):
    text = message.text
    self.query_one(OutputLog).append_text(f"> {text}")  # echo input
    self.query_one(InputArea).clear()
    
    response = self._core.handle_input(text)
    if response.quit:
        self.exit()
    elif response.clear_output:
        self.query_one(OutputLog).clear()
    elif response.text:
        self.query_one(OutputLog).append_text(response.text)
    elif response.send_to_llm:
        self.run_worker(lambda: self._stream_llm(text), thread=True)

_stream_llm(text):
    try:
        for event in self._core.stream_llm(text):
            self.call_from_thread(self._handle_stream_event, event)
    except Exception as e:
        self.call_from_thread(self._show_error, str(e))
```

## DATA — Return Values

- `ICoderApp.compose()` yields Textual widgets
- `InputArea.InputSubmitted.text` — the submitted text string
- Stream events rendered as text in `OutputLog`

## Tests — `tests/icoder/test_app_pilot.py`

```python
import pytest
from textual.pilot import Pilot

# Helper to create app with FakeLLM
@pytest.fixture
def icoder_app(fake_llm, event_log):
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    return ICoderApp(app_core)

# Test app launches without error
async def test_app_launches(icoder_app):
    async with icoder_app.run_test() as pilot:
        assert icoder_app.is_running

# Test input area is focused on startup
async def test_input_focused_on_startup(icoder_app):
    async with icoder_app.run_test() as pilot:
        focused = icoder_app.focused
        assert isinstance(focused, InputArea)

# Test output area is above input area (layout)
async def test_layout_structure(icoder_app):
    async with icoder_app.run_test() as pilot:
        output = icoder_app.query_one(OutputLog)
        input_area = icoder_app.query_one(InputArea)
        assert output.region.y < input_area.region.y

# Test type text + Enter → text appears in output, input clears
async def test_submit_text(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("hello world")
        await pilot.press("enter")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        # Output should contain the echoed input
        # Input area should be cleared

# Test /clear + Enter → output log is cleared
async def test_clear_command(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("/help")
        await pilot.press("enter")
        await pilot.pause()
        await pilot.type("/clear")
        await pilot.press("enter")
        await pilot.pause()
        # Output should be cleared

# Test /quit + Enter → app exits
async def test_quit_command(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("/quit")
        await pilot.press("enter")
        await pilot.pause()
        # App should have exited

# Test Shift-Enter inserts newline (does not submit)
async def test_shift_enter_newline(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("line1")
        await pilot.press("shift+enter")
        await pilot.type("line2")
        input_area = icoder_app.query_one(InputArea)
        assert "\n" in input_area.text

# Test multi-line input submits as one message
async def test_multiline_submit(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("line1")
        await pilot.press("shift+enter")
        await pilot.type("line2")
        await pilot.press("enter")
        await pilot.pause()
        # Both lines should appear in output

# Test streaming LLM response appears in output
async def test_llm_streaming(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("hello")
        await pilot.press("enter")
        await pilot.pause(delay=0.5)  # Give worker time
        output = icoder_app.query_one(OutputLog)
        # Should contain fake LLM response text
```

## LLM Prompt

```
You are implementing Step 7 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Implement ui/styles.py — CSS string for vertical layout
2. Implement ui/widgets/output_log.py — OutputLog(RichLog) with append_text() and append_tool_use()
3. Implement ui/widgets/input_area.py — InputArea(TextArea) with Enter=submit, Shift-Enter=newline
4. Implement ui/app.py — ICoderApp(App) wiring UI events to AppCore
5. Update cli/commands/icoder.py to actually launch ICoderApp
6. Write pilot integration tests in tests/icoder/test_app_pilot.py
7. Run pylint, mypy, pytest to verify all checks pass

Key details:
- InputArea posts InputSubmitted message on Enter, inserts newline on Shift-Enter
- ICoderApp.compose() = OutputLog + InputArea (vertical layout)
- LLM streaming uses run_worker(thread=True) + call_from_thread()
- MCP tool display: ⚙ name(args) → done (compact one-line)
- Error handling: catch exceptions in worker, display in output, app stays alive
- Tests use Textual's async with app.run_test() pattern with FakeLLMService
- All pilot tests are async functions

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
