# Step 2 — Status hint widget below InputArea

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Add a `Static` widget below `InputArea` showing `\ + Enter = newline` when input is empty, hidden when input has text.

## WHERE

- **Modify:** `src/mcp_coder/icoder/ui/app.py` — `compose()` and new `on_text_area_changed` handler
- **Modify:** `src/mcp_coder/icoder/ui/styles.py` — CSS for `#input-hint` and `InputArea` border removal
- **Modify:** `tests/icoder/test_app_pilot.py` — hint visibility tests

## WHAT

### `app.py`

```python
def compose(self) -> ComposeResult:
    yield OutputLog()
    yield Static(id="streaming-tail")
    yield CommandAutocomplete()
    yield InputArea(registry=..., event_log=...)
    yield Static(r"\ + Enter = newline", id="input-hint")  # NEW
```

```python
def on_text_area_changed(self) -> None:
    """Toggle input hint visibility based on whether input is empty."""
```

### `styles.py`

```css
InputArea {
    border: none;
}

#input-hint {
    height: 1;
    background: #1e1e1e;
    color: #666666;
    text-align: right;
}

#input-hint.hidden {
    display: none;
}
```

### `test_app_pilot.py`

```python
async def test_hint_visible_when_input_empty(icoder_app: ICoderApp) -> None:
async def test_hint_hidden_when_input_has_text(icoder_app: ICoderApp) -> None:
async def test_hint_reappears_after_submit(icoder_app: ICoderApp) -> None:
```

## HOW

- `ICoderApp.on_text_area_changed` is automatically called by Textual when `TextArea.Changed` bubbles up from `InputArea`
- Toggle via `add_class("hidden")` / `remove_class("hidden")` on the `#input-hint` Static
- Check `self.query_one(InputArea).text` to decide visibility

## ALGORITHM

```
def on_text_area_changed(self):
    hint = self.query_one("#input-hint", Static)
    input_area = self.query_one(InputArea)
    if input_area.text:
        hint.add_class("hidden")
    else:
        hint.remove_class("hidden")
```

## DATA

- Hint text: `\ + Enter = newline` (raw string to avoid escaping)
- CSS class `hidden` controls `display: none`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement the status hint widget below InputArea.

1. Write tests first in tests/icoder/test_app_pilot.py — hint visible when empty, hidden with text, reappears after submit.
2. Add the Static widget in app.py compose().
3. Add on_text_area_changed handler in ICoderApp.
4. Add CSS in styles.py (including `InputArea { border: none; }` to remove the default TextArea border).
5. Run all code quality checks (pylint, pytest, mypy). Fix any issues.
6. Commit: "feat(icoder): add newline hint below input area (#754)"
```
