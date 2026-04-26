# Step 2 — Scroll cursor visible + wrapped auto-grow height

> **Ref:** [summary.md](summary.md) • Issue #896 §2 & §3

## Goal

Two one-line fixes in `on_text_area_changed`:

1. Use `self.virtual_size.height` (visual/wrapped lines) instead of `self.document.line_count` (logical lines) for auto-grow height calculation
2. Call `self.scroll_cursor_visible()` after height adjustment to keep cursor in view

## WHERE

- `src/mcp_coder/icoder/ui/widgets/input_area.py` — `on_text_area_changed`, lines 70–76
- `tests/icoder/test_widgets.py` — updated/new test for wrapped-line auto-grow

## WHAT

### Modified: `on_text_area_changed` (lines 74–76)

**Current:**
```python
line_count = self.document.line_count
max_lines = max(1, self.screen.size.height // 3)
self.styles.height = min(line_count + 2, max_lines)
```

**New:**
```python
visual_lines = self.virtual_size.height
max_lines = max(1, self.screen.size.height // 3)
self.styles.height = min(visual_lines + 2, max_lines)
self.scroll_cursor_visible()
```

> The `+2` offset accounts for widget chrome (border + padding) and remains valid with visual line counts.

## HOW

- `self.virtual_size.height` — Textual `Widget` property that returns the height of the virtual (scrollable) content in rows. For `TextArea`, this accounts for soft-wrapped lines via `WrappedDocument`.
- `self.scroll_cursor_visible()` — Textual `TextArea` built-in method. Scrolls the minimum amount to make the cursor visible. No-op when cursor is already in view.

> If direct calling doesn't scroll reliably in testing (because layout reflow hasn't completed), use `self.call_after_refresh(self.scroll_cursor_visible)` as a fallback.

## ALGORITHM

```
1. Guard: return if no screen
2. visual_lines = self.virtual_size.height  # wrapped line count
3. max_lines = screen_height // 3
4. self.styles.height = min(visual_lines + 2, max_lines)
5. self.scroll_cursor_visible()
6. (continue to autocomplete logic)
```

## DATA

- `self.virtual_size` — `Size(width, height)` from Textual, where `.height` is the visual row count
- `scroll_cursor_visible()` — returns `None`, side-effect only

## Tests (TDD — write first)

### Updated test: `test_input_area_grows_with_multiline`
The existing test already verifies height changes with multiline content. It should still pass since `virtual_size.height >= document.line_count`.

### New test: `test_input_area_grows_with_wrapped_long_line`
- Use `run_test(size=(40, 20))` to guarantee a known widget width for deterministic wrapping
- Insert a single long line (no `\n`) that clearly exceeds 40 characters to ensure wrapping occurs
- Assert that `styles.height` is greater than what `document.line_count + 2` would give (i.e., it accounts for visual wrapping)
- This validates that `virtual_size.height` is used, not `document.line_count`

### Scroll test
- `scroll_cursor_visible()` is difficult to assert directly in a unit test (it's a rendering-level concern). The snapshot tests in step 3 provide visual verification. For unit-level coverage, confirming the method is called (or simply that no error is raised during multiline editing) suffices — the existing multiline tests exercise this code path.

## Commit message

```
feat(icoder): auto-grow uses wrapped line count, scroll cursor visible (#896)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: two one-line changes in on_text_area_changed:
- Replace self.document.line_count with self.virtual_size.height for auto-grow
- Add self.scroll_cursor_visible() after height adjustment

TDD approach:
1. First, add test_input_area_grows_with_wrapped_long_line in tests/icoder/test_widgets.py
2. Then make the two-line change in src/mcp_coder/icoder/ui/widgets/input_area.py
3. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
```
