# Step 2: InputArea Auto-Grow

> **Context:** See `pr_info/steps/summary.md` for full issue context (Issue #683).

## Goal

Make the InputArea grow dynamically with content instead of staying at 1 line. Remove the fixed `max-height: 5` from CSS and add a Python handler that sizes the widget to `min(line_count, screen_height // 3)`.

## LLM Prompt

```
Implement Step 2 of Issue #683 (see pr_info/steps/summary.md for context).

Two changes:
1. In styles.py, remove `max-height: 5;` from the InputArea CSS rule.
2. In input_area.py, add an on_text_area_changed handler that sets self.styles.height to min(line_count, screen_height // 3). Use self.document.line_count for lines and self.screen.size.height for screen height. Guard self.screen access with an early return (the handler can fire before the widget is mounted).

Add a test in test_widgets.py that verifies the input area height changes after inserting multiline text via Shift+Enter.

Run all quality checks after.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/ui/styles.py` | Modify |
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | Modify |
| `tests/icoder/test_widgets.py` | Modify (add test) |

## WHAT

### `styles.py` — remove max-height

```python
CSS: str = """
OutputLog {
    height: 1fr;
    background: #1e1e1e;
    color: #d4d4d4;
}

InputArea {
    height: auto;
    background: #1e1e1e;
    color: #d4d4d4;
}
"""
```

### `input_area.py` — add height handler

```python
def on_text_area_changed(self) -> None:
    """Resize height to match content, capped at 1/3 of screen."""
    if not self.screen:
        return
    line_count = self.document.line_count
    max_lines = self.screen.size.height // 3
    self.styles.height = min(line_count, max_lines)
```

## ALGORITHM

```
on text change:
    if screen not available: return early
    lines = document.line_count
    cap = screen.height // 3
    self.styles.height = min(lines, cap)
```

## DATA

- `self.document.line_count` → `int` (number of lines in the text area)
- `self.screen.size.height` → `int` (terminal height in rows)
- `self.styles.height` → set to `int` (Textual interprets as row count)

## HOW

- `on_text_area_changed` is Textual's built-in handler name for `TextArea.Changed` messages — no decorator or registration needed, just define the method.
- No new imports required.

## Test

Add to `tests/icoder/test_widgets.py`:

```python
@pytest.mark.asyncio
async def test_input_area_grows_with_multiline() -> None:
    """InputArea height increases when multiline text is entered."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        initial_height = input_area.styles.height
        input_area.insert("line1")
        await pilot.press("shift+enter")
        input_area.insert("line2")
        await pilot.press("shift+enter")
        input_area.insert("line3")
        await pilot.pause()
        assert input_area.styles.height != initial_height
```

## Verification

- New test must pass
- All existing widget tests must still pass
- All quality checks (pylint, mypy, pytest unit tests) must pass

## Commit

`feat(icoder): auto-grow input area with content up to 1/3 screen height`
