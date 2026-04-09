# Step 1 — Backslash+Enter newline escape logic

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

When the user presses Enter and the input ends with `\`, insert a newline instead of submitting. `\\` + Enter escapes to submit with a literal trailing `\`.

## WHERE

- **Modify:** `src/mcp_coder/icoder/ui/widgets/input_area.py` — `InputArea._on_key`, Enter handler
- **Modify:** `tests/icoder/test_widgets.py` — new parametrized tests

## WHAT

### `input_area.py` — new helper + modified Enter handler

No new public functions. Add a module-level helper:

```python
def _count_trailing_backslashes(text: str) -> int:
    """Count consecutive trailing backslashes in text."""
```

Modify the `enter` key block in `_on_key` (lines 162–181).

### `test_widgets.py` — parametrized test

```python
@pytest.mark.parametrize("input_text, expect_submit, expected_text", [...])
async def test_backslash_enter_newline(input_text, expect_submit, expected_text) -> None:
```

## HOW

The backslash check slots in **after** autocomplete dismissal (line 174) and **before** submit (line 177). It operates on `self.text` (raw, not stripped).

## ALGORITHM

```
raw = self.text
trailing = count trailing backslashes in raw
if trailing > 0:
    text_without_last_backslash = raw[:-1]
    if trailing is odd:
        # Replace the trailing \ with a newline
        load text_without_last_backslash
        end = self.document.end  # Recalculate after load_text changed the document
        _replace_via_keyboard("\n", end, end)
        return (do not submit)
    else:
        # Even: strip one \, fall through to existing submit code
        set self.text to text_without_last_backslash
        # Fall through — existing code at line 177 will .strip() and submit
```

For the odd case, the simplest approach: use `self.load_text(raw[:-1])` to remove the `\`, then recalculate `end = self.document.end` (since `load_text` replaced the document), then `self._replace_via_keyboard("\n", end, end)` to insert the newline at the new end position.

## DATA

- `_count_trailing_backslashes("hello\\")` → `2`
- `_count_trailing_backslashes("hello\\\\\\")` → `3`
- `_count_trailing_backslashes("hello")` → `0`

## Test cases (parametrized)

| Input text | Action | Result |
|-----------|--------|--------|
| `hello\` | Enter | No submit, text becomes `hello\n` (cursor after newline) |
| `hello\\` | Enter | Submit with text `hello\` |
| `hello\\\` | Enter | No submit, text becomes `hello\\\n` |
| `hello\\\\` | Enter | Submit with text `hello\\\` |
| `\` | Enter | No submit, text becomes `\n` |
| `hello` | Enter | Submit with text `hello` (unchanged behavior) |
| ` ` (whitespace only) | Enter | No submit (existing behavior, text.strip() is empty) |

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement the backslash+Enter newline escape in InputArea._on_key.

1. Write tests first in tests/icoder/test_widgets.py — parametrized test for all cases in the table.
2. Add _count_trailing_backslashes() helper in input_area.py.
3. Modify the Enter handler to check trailing backslashes before submitting.
4. Run all code quality checks (pylint, pytest, mypy). Fix any issues.
5. Commit: "feat(icoder): backslash+Enter inserts newline (#754)"
```
