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
cursor_loc = self.selection.end          # (row, col) Location
# count backslashes before cursor using text-before-cursor
trailing = _count_trailing_backslashes(text_before_cursor)
```

Note: `_count_trailing_backslashes` is called on the substring of text before the cursor position, extracted using the cursor's `(row, col)` Location.

## HOW

The cursor position is available via `self.selection.end` which returns a `(row, col)` Location. To get the text before the cursor, extract the substring using document lines or flat offset. The key insight is to use `_replace_via_keyboard` for mutations instead of `load_text`, since `load_text` destroys undo history.

```python
cursor_loc = self.selection.end          # (row, col) tuple
row, col = cursor_loc
# backslash is one character before cursor
backslash_loc = (row, col - 1)           # assumes backslash is on same line

# For odd backslash (insert newline):
self._replace_via_keyboard("\n", backslash_loc, cursor_loc)

# For even backslash (remove backslash, then submit):
self._replace_via_keyboard("", backslash_loc, cursor_loc)
```

**Why `_replace_via_keyboard`?** It preserves undo history and is already used by the `Shift+Enter` handler. Using `load_text` would reset the undo stack, breaking user expectations for Ctrl+Z.

## ALGORITHM (Enter handler, backslash section)

```
1. event.stop() + event.prevent_default()
2. cursor_loc = self.selection.end  # (row, col) tuple
3. Compute the location of the character before cursor (the backslash):
   row, col = cursor_loc; backslash_loc = (row, col - 1)
4. Extract text before cursor to count trailing backslashes
5. trailing = _count_trailing_backslashes(text_before_cursor)
6. if trailing == 0 → submit as normal (strip, post message, clear)
7. if trailing odd → self._replace_via_keyboard("\n", backslash_loc, cursor_loc)
   — single atomic edit: removes backslash, inserts newline, preserves undo
8. if trailing even → compute backslash_loc (one character before cursor)
   → self._replace_via_keyboard("", backslash_loc, cursor_loc) to remove backslash
   → text = self.text.strip()
   → self.post_message(InputArea.Submitted(text))
   → self.clear()
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
