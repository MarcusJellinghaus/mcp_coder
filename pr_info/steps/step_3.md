# Step 3: UI wiring — default border CSS and runtime color application

> See [summary.md](summary.md) for full context (Issue #798).

## Goal

Add the default `round #666666` border to InputArea CSS, and wire `ICoderApp` to apply `app_core.prompt_color` to the InputArea border on mount and after every input.

## LLM Prompt

```
Implement Step 3 of Issue #798 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).
Add default border CSS and UI color application logic. This step modifies UI files.
Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- `src/mcp_coder/icoder/ui/styles.py` — add border to InputArea CSS
- `src/mcp_coder/icoder/ui/app.py` — add `_apply_prompt_border()`, call from two places

## WHAT

### CSS change in `styles.py`

```css
InputArea {
    height: auto;
    background: #1e1e1e;
    color: #d4d4d4;
    border: round #666666;
}
```

### `_apply_prompt_border()` in `app.py`

```python
def _apply_prompt_border(self) -> None:
    """Apply current prompt color as InputArea border."""
    from textual.color import Color
    color = Color.parse(self._core.prompt_color)
    self.query_one(InputArea).styles.border = ("round", color)
```

### Call sites

1. **`on_mount()`** — after existing startup code, before `self.query_one(InputArea).focus()`
2. **`on_input_area_input_submitted()`** — after `response = self._core.handle_input(text)`, before the if/elif chain

## ALGORITHM

```
1. _apply_prompt_border reads self._core.prompt_color (always a valid hex)
2. Parses it via Color.parse()
3. Sets input_area.styles.border = ("round", parsed_color)
4. Called on_mount → initial border (covers --initial-color and default)
5. Called after every handle_input → color changes take effect immediately
```

## DATA

- `app_core.prompt_color` always returns a valid hex string
- `Color.parse()` on a valid hex never fails
- Border tuple: `("round", Color)` — Textual's border API

## NOTES

- The CSS `border: round #666666` provides the default before `on_mount` runs
- `_apply_prompt_border()` overrides it at runtime (supports `--initial-color` and `/color`)
- The `on_text_area_changed` height calc uses `line_count + 2` which already accounts for border chrome — verify with existing snapshot tests
- Existing snapshot SVGs will need regeneration since the border is new visual content — update with `pytest --snapshot-update` if needed
- Import `Color` only inside the method to keep the module-level import light

## SNAPSHOT TESTS

- Adding `border: round #666666` to InputArea CSS will change the visual output
- Existing snapshot tests (if any) must be regenerated in this step: `pytest --snapshot-update -k snapshot`
- Verify snapshot diffs only show the new border, no unrelated changes
- If no snapshot tests exist for InputArea, note this and move on

## Commit message

```
feat(icoder): add colored round border to InputArea (#798)
```
