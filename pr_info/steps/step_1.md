# Step 1 — `\+Enter` newline at cursor position

> **Ref:** [summary.md](summary.md) • Issue #896 §1

## Goal

Change the Enter handler so that `\+Enter` checks for backslashes immediately **before the cursor**, not at the end of the full text. On odd count: consume last `\`, insert `\n` at cursor position. On even count: strip one `\`, submit.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/input_area.py` — `_on_key` method, lines 180–209
- `tests/icoder/test_widgets.py` — new test cases

## WHAT

No new functions. The existing `_count_trailing_backslashes(text)` is reused on a **substring** (text before cursor).

### Modified: `_on_key` Enter handler (lines 195–209)

Current logic:
```python
raw = self.text
trailing = _count_trailing_backslashes(raw)
```

New logic — compute text before cursor, count backslashes there:
```python
cursor_loc = self.selection.end          # (row, col) tuple
before, after = self._split_at_cursor()  # helper or inline
trailing = _count_trailing_backslashes(before)
```

## HOW

The cursor position is available via `self.selection.end` which returns a `(row, col)` Location. To get the flat text offset, use `self.document.get_index_from_location(location)` or reconstruct from text lines. The simplest approach:

```python
# Get text before and after cursor using document lines
row, col = self.selection.end
lines = self.text.split("\n")  # or self.document access
before = "\n".join(lines[:row]) + ("\n" if row > 0 else "") + lines[row][:col]
after = lines[row][col:] + "\n".join([""] + lines[row+1:]) if row < len(lines)-1 else lines[row][col:]
```

Or more simply, convert to flat offset:
```python
text = self.text
offset = sum(len(lines[i]) + 1 for i in range(row)) + col  # +1 for \n
before = text[:offset]
after = text[offset:]
```

## ALGORITHM (Enter handler, backslash section)

```
1. event.stop() + event.prevent_default()
2. cursor_loc = self.selection.end  # (row, col)
3. Compute flat offset from cursor_loc; split self.text into before/after
4. trailing = _count_trailing_backslashes(before)
5. if trailing == 0 → submit as normal (strip, post message, clear)
6. if trailing odd → remove last \ from before, rebuild text as before[:-1] + "\n" + after, load_text + reposition cursor
7. if trailing even → remove last \ from before, rebuild text as before[:-1] + after, submit stripped text
```

## DATA

- Input: `self.text`, `self.selection.end` — existing TextArea state
- Output: either newline inserted at cursor (no submission) or text submitted (message posted)
- `_count_trailing_backslashes` signature unchanged: `(text: str) -> int`

## Tests (TDD — write first)

### New test: `test_backslash_enter_mid_text_inserts_newline`
- Load text `"ABC \DEF"` (backslash between ABC and DEF)
- Position cursor after the `\` (i.e., after `"ABC \"`)
- Press Enter
- Assert: no submission, text becomes `"ABC \nDEF"` (backslash consumed, newline inserted)

### New test: `test_backslash_enter_mid_text_double_backslash_submits`
- Load text `"ABC \\DEF"` (two backslashes)
- Position cursor after `"ABC \\"` 
- Press Enter
- Assert: submission with text `"ABC \DEF"` (one backslash stripped, rest submitted)

### Existing tests must still pass
- All parametrized `test_backslash_enter_newline` cases use cursor at end → they exercise the same code path with `after == ""`, so they should pass unchanged.

## Commit message

```
feat(icoder): \+Enter inserts newline at cursor position (#896)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: make \+Enter insert a newline at the cursor position instead of only working at end-of-text.

TDD approach:
1. First, add the new test cases in tests/icoder/test_widgets.py (mid-text backslash+enter tests)
2. Then modify the Enter handler in src/mcp_coder/icoder/ui/widgets/input_area.py
3. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
4. Verify existing backslash+enter tests still pass
```
