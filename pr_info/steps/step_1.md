# Step 1: OutputLog Wrap + Explicit Color Scheme

> **Context:** See `pr_info/steps/summary.md` for full issue context (Issue #683).

## Goal

Fix two independent visual bugs: (a) long lines in OutputLog require horizontal scrolling, (b) text is invisible in VS Code terminal due to missing explicit colors.

## LLM Prompt

```
Implement Step 1 of Issue #683 (see pr_info/steps/summary.md for context).

Two changes:
1. In OutputLog.__init__, pass wrap=True to the RichLog super().__init__().
2. In styles.py, add explicit background (#1e1e1e) and color (#d4d4d4) to both OutputLog and InputArea CSS rules.

No test changes needed — existing widget tests cover OutputLog construction. Run all quality checks after.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/ui/widgets/output_log.py` | Modify |
| `src/mcp_coder/icoder/ui/styles.py` | Modify |

## WHAT

### `output_log.py` — OutputLog.__init__

```python
def __init__(self, **kwargs: Any) -> None:
    super().__init__(wrap=True, **kwargs)  # was: super().__init__(**kwargs)
    self._recorded: list[str] = []
```

### `styles.py` — CSS constant

```python
CSS: str = """
OutputLog {
    height: 1fr;
    background: #1e1e1e;
    color: #d4d4d4;
}

InputArea {
    height: auto;
    max-height: 5;
    background: #1e1e1e;
    color: #d4d4d4;
}
"""
```

## HOW

- `wrap=True` is a RichLog constructor parameter — no imports needed
- CSS colors are Textual CSS properties — no Python changes needed for colors
- Existing `STYLE_USER_INPUT` / `STYLE_TOOL_OUTPUT` in `app.py` override these defaults locally

## Verification

- Existing tests in `tests/icoder/test_widgets.py` must still pass
- All quality checks (pylint, mypy, pytest unit tests) must pass

## Commit

`fix(icoder): enable line wrapping and explicit colors in TUI widgets`
