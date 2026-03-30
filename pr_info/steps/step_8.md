# Step 8: ICoderApp + Pilot Integration Tests

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Steps 1-7 (all core, services, CLI, widgets)

## Goal
Implement `ICoderApp` — the Textual `App` that wires UI events to `AppCore`. Add async bridging for LLM streaming. Update `cli/commands/icoder.py` to launch the app. Add Textual pilot integration tests.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/ui/app.py`
- `tests/icoder/test_app_pilot.py`

### Modified files
- `src/mcp_coder/cli/commands/icoder.py` — add actual `ICoderApp` launch

## WHAT — Main Functions and Signatures

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
- Worker errors caught and displayed in output area (app stays alive)

### Key Textual patterns
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
        input_area = icoder_app.query_one(InputArea)
        # Verify echoed input appears in OutputLog
        assert "> hello world" in output.lines
        # Verify input area is cleared
        assert input_area.text == ""

# Test /clear + Enter → output log is cleared
async def test_clear_command(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("/help")
        await pilot.press("enter")
        await pilot.pause()
        await pilot.type("/clear")
        await pilot.press("enter")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        # Output should be empty after clear
        assert len(output.lines) == 0

# Test /quit + Enter → app exits
async def test_quit_command(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("/quit")
        await pilot.press("enter")
        await pilot.pause()
    # App should no longer be running after exiting the context
    assert not icoder_app.is_running

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
        output = icoder_app.query_one(OutputLog)
        # Both lines should appear in echoed output
        assert "line1" in output.lines
        assert "line2" in output.lines

# Test streaming LLM response appears in output
async def test_llm_streaming(icoder_app):
    async with icoder_app.run_test() as pilot:
        await pilot.type("hello")
        await pilot.press("enter")
        await pilot.pause(delay=0.5)  # Give worker time
        output = icoder_app.query_one(OutputLog)
        # Should contain fake LLM response text
        assert "fake response" in output.lines
```

## LLM Prompt

```
You are implementing Step 8 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Implement ui/app.py — ICoderApp(App) wiring UI events to AppCore
2. Update cli/commands/icoder.py to actually launch ICoderApp (lazy import with clear error if textual not installed)
3. Write pilot integration tests in tests/icoder/test_app_pilot.py
4. Run pylint, mypy, pytest to verify all checks pass

Key details:
- ICoderApp.compose() = OutputLog + InputArea (vertical layout)
- LLM streaming uses run_worker(thread=True) + call_from_thread()
- MCP tool display: ⚙ name(args) → done (compact one-line)
- Error handling: catch exceptions in worker, display in output, app stays alive
- Tests use Textual's async with app.run_test() pattern with FakeLLMService
- All pilot tests are async functions
- Pilot tests must have concrete assertions (not comment placeholders)

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
