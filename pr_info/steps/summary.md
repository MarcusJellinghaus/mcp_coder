# Issue #896 — InputArea: cursor-position newline, scroll, wrapped auto-grow

## Goal

Three targeted improvements to `InputArea` in the iCoder TUI:

1. **`\+Enter` at cursor position** — currently only works when `\` is at end of text; should work wherever the cursor is
2. **Scroll cursor visible** — after auto-grow resizes the widget, ensure the cursor stays in view
3. **Wrapped-line auto-grow** — use visual (wrapped) line count instead of logical line count for height calculation

## Architectural / Design Changes

**No new files, classes, or abstractions are introduced.** All changes are localized edits within the existing `InputArea` widget.

- **`_count_trailing_backslashes`** — the existing helper is **reused unchanged**. The Enter handler is changed to pass it the text-before-cursor (a substring) instead of the full text. This turns "trailing backslashes in full text" into "backslashes immediately before cursor" with zero new code.
- **`on_text_area_changed`** — two one-line changes:
  - `self.document.line_count` → `self.virtual_size.height` (visual wrapped lines instead of logical lines)
  - Add `self.scroll_cursor_visible()` call after height adjustment (Textual built-in, no-op when cursor is already visible)
- **Enter handler in `_on_key`** — instead of operating on `self.text` (full text) and appending newline at end, it now:
  - Computes text before/after cursor
  - Counts backslashes before cursor using the existing helper
  - Strips backslash and inserts newline at cursor position (or strips backslash and submits)

**Design principle:** No new helpers, no new state, no new abstractions. Each fix is a surgical change to existing logic.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | All 3 fixes (Enter handler, scroll, auto-grow) |
| `tests/icoder/test_widgets.py` | New tests for mid-cursor `\+Enter`; update auto-grow test for wrapped lines |
| `tests/icoder/__snapshots__/*.svg` | Snapshot updates if auto-grow height changes (regenerated via `--snapshot-update`) |

## Steps

| Step | Description |
|------|-------------|
| 1 | `\+Enter` newline at cursor position (TDD: tests first, then implementation) |
| 2 | Scroll cursor visible + wrapped auto-grow height (TDD: tests first, then implementation) |
| 3 | Snapshot update — regenerate any affected SVG baselines |
