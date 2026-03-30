# Step 7: UI Widgets (styles, OutputLog, InputArea)

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Steps 1-6 (all core, services, CLI)

## Goal
Implement the Textual UI widgets: CSS styles, `OutputLog`, and `InputArea`. These are standalone widgets with no dependency on `ICoderApp`. Add widget unit and integration tests.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/ui/styles.py`
- `src/mcp_coder/icoder/ui/widgets/output_log.py`
- `src/mcp_coder/icoder/ui/widgets/input_area.py`
- `tests/icoder/test_widgets.py`

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

## HOW — Integration Points

- `OutputLog` extends `RichLog` with helper methods for structured output
- `InputArea` overrides `_on_key()` to intercept Enter vs Shift-Enter
- `InputSubmitted` is a Textual `Message` — auto-dispatched to parent via naming convention
- CSS: `OutputLog` gets `height: 1fr`, `InputArea` gets `height: auto` with max ~5 lines
- These widgets are independent of `ICoderApp` and can be tested in isolation

## Tests — `tests/icoder/test_widgets.py`

```python
import pytest
from textual.app import App, ComposeResult

# Minimal test app that hosts the widgets
class WidgetTestApp(App):
    def compose(self) -> ComposeResult:
        yield OutputLog()
        yield InputArea()

# Test OutputLog append_text adds content
async def test_output_log_append_text():
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        output = app.query_one(OutputLog)
        output.append_text("hello")
        # Verify content was added (line count > 0)

# Test OutputLog append_tool_use formats correctly
async def test_output_log_append_tool_use():
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        output = app.query_one(OutputLog)
        output.append_tool_use("read_file", "path.py", "ok")

# Test InputArea Enter posts InputSubmitted message
async def test_input_area_enter_submits():
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        await pilot.type("hello")
        await pilot.press("enter")
        await pilot.pause()
        # Input area should be cleared after submit

# Test InputArea Shift-Enter inserts newline (does not submit)
async def test_input_area_shift_enter_newline():
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        await pilot.type("line1")
        await pilot.press("shift+enter")
        await pilot.type("line2")
        input_area = app.query_one(InputArea)
        assert "\n" in input_area.text
```

## LLM Prompt

```
You are implementing Step 7 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Implement ui/styles.py — CSS string for vertical layout
2. Implement ui/widgets/output_log.py — OutputLog(RichLog) with append_text() and append_tool_use()
3. Implement ui/widgets/input_area.py — InputArea(TextArea) with Enter=submit, Shift-Enter=newline
4. Write widget tests in tests/icoder/test_widgets.py
5. Run pylint, mypy, pytest to verify all checks pass

Key details:
- OutputLog and InputArea are standalone widgets, tested independently of ICoderApp
- InputArea posts InputSubmitted message on Enter, inserts newline on Shift-Enter
- CSS defines vertical layout with OutputLog taking most space
- Tests use a minimal WidgetTestApp host for the widgets

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
