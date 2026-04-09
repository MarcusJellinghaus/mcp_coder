# Step 3 — `/help` keyboard shortcuts section

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Add a "Keyboard shortcuts" section to `/help` output.

## WHERE

- **Modify:** `src/mcp_coder/icoder/core/commands/help.py` — `handle_help` closure
- **Modify:** `tests/icoder/test_app_core.py` — assert `/help` output contains shortcuts

## WHAT

### `help.py`

Append keyboard shortcuts after the command listing:

```python
lines.append("")
lines.append("Keyboard shortcuts:")
lines.append(r"  \ + Enter   - Insert newline")
lines.append("  Shift+Enter - Insert newline (terminal support varies)")
```

### Test

```python
def test_help_includes_keyboard_shortcuts(app_core: AppCore) -> None:
    response = app_core.handle_input("/help")
    assert "Keyboard shortcuts:" in response.text
    assert "Insert newline" in response.text
```

## HOW

Append lines to the existing `lines` list in `handle_help`. No structural changes.

## ALGORITHM

```
# after the for-loop that lists commands:
lines.append("")
lines.append("Keyboard shortcuts:")
lines.append(r"  \ + Enter   - Insert newline")
lines.append("  Shift+Enter - Insert newline (terminal support varies)")
```

## DATA

Expected `/help` output (partial):

```
Available commands:
  /help - Show available commands
  /clear - Clear the output log
  /quit - Exit iCoder

Keyboard shortcuts:
  \ + Enter   - Insert newline
  Shift+Enter - Insert newline (terminal support varies)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Add keyboard shortcuts section to /help output.

1. Write test first in tests/icoder/test_app_core.py — assert /help contains "Keyboard shortcuts:" and both shortcut lines.
2. Modify help.py to append the shortcuts section.
3. Run all code quality checks (pylint, pytest, mypy). Fix any issues.
4. Commit: "feat(icoder): add keyboard shortcuts to /help (#754)"
```
