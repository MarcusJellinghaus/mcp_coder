# Step 2: InputArea Up/Down Integration + Widget Key Tests

> **Reference**: See `pr_info/steps/summary.md` for full context. Step 1 must be completed first.

## Goal

Integrate `CommandHistory` into `InputArea`. Intercept Up/Down arrow keys with boundary-line detection. Add async widget tests for the key behavior.

## WHERE

| File | Action |
|------|--------|
| `tests/icoder/test_widgets.py` | **MODIFY** — add history key tests |
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | **MODIFY** — add history + key handling |

## WHAT — Changes to `InputArea`

### New Import

```python
from mcp_coder.icoder.core.command_history import CommandHistory
```

### New Attribute

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.history = CommandHistory()
```

### New Key Handling in `_on_key()`

Add two `elif` branches after the existing `shift+enter` handling, before the `await super()._on_key(event)` fallthrough:

```python
if event.key == "up":
    row, _col = self.cursor_location
    if row == 0:  # cursor on first line
        result = self.history.up(self.text)
        event.stop()
        event.prevent_default()
        if result is not None:
            self.clear()
            self.insert(result)
        return

if event.key == "down":
    row, _col = self.cursor_location
    last_row = self.document.line_count - 1
    if row == last_row:  # cursor on last line
        result = self.history.down()
        event.stop()
        event.prevent_default()
        if result is not None:
            self.clear()
            self.insert(result)
        return
```

## ALGORITHM — Boundary Detection (pseudocode)

```
on_key(up):
    if cursor_row != 0: delegate to parent (normal cursor movement)
    result = history.up(current_text)
    stop event propagation (prevent TextArea default behavior)
    if result is not None: replace text area content with result
    return

on_key(down):
    if cursor_row != last_row: delegate to parent (normal cursor movement)
    result = history.down()
    stop event propagation (prevent TextArea default behavior)
    if result is not None: replace text area content with result
    return
```

## DATA — No New Types

Uses existing `self.cursor_location -> tuple[int, int]` and `self.document.line_count -> int` from Textual's `TextArea`.

## HOW — Integration Points

- `CommandHistory` is imported from `core.command_history`
- `InputArea.__init__` creates the instance
- Key interception happens in the existing `_on_key()` method
- `self.clear()` + `self.insert(result)` replaces content (existing TextArea API)

## Tests to Add (`tests/icoder/test_widgets.py`)

Use existing `WidgetTestApp` pattern. Tests:

1. **`test_input_area_up_arrow_restores_history`** — Submit "hello" via insert+enter, press Up, verify text becomes "hello"
2. **`test_input_area_down_arrow_restores_draft`** — Submit "cmd", type "draft", press Up (see "cmd"), press Down (see "draft")
3. **`test_input_area_up_arrow_no_history_does_nothing`** — Press Up on empty history, text stays empty
4. **`test_input_area_up_down_multiline_cursor_movement`** — Insert `"line1\nline2\nline3"` (cursor ends at last line, line 2). Press Up to move cursor to line 1 (middle line) — normal cursor movement, not history. Press Up again to move to line 0 — still normal cursor movement. Verify text content is unchanged (no history substitution occurred).

Note: These tests need a `SubmitApp` that captures `InputSubmitted` messages AND calls `history.add()` to simulate the full flow (since in production the app calls `history.add()`). Alternatively, directly call `input_area.history.add()` in the test setup.

## LLM Prompt

```
Implement Step 2 of issue #631 (iCoder command history).
See pr_info/steps/summary.md for full context and pr_info/steps/step_2.md for this step's spec.

TDD approach:
1. Add history key tests to tests/icoder/test_widgets.py as specified in step_2.md
2. Modify src/mcp_coder/icoder/ui/widgets/input_area.py to add CommandHistory and Up/Down interception
3. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
4. Commit when all checks pass
```
