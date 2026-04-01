# Step 1: CommandHistory Class + Unit Tests

> **Reference**: See `pr_info/steps/summary.md` for full context.

## Goal

Create the `CommandHistory` class in `core/` with its complete API, and comprehensive unit tests. TDD: write tests first, then implement.

## WHERE

| File | Action |
|------|--------|
| `tests/icoder/test_command_history.py` | **CREATE** — unit tests |
| `src/mcp_coder/icoder/core/command_history.py` | **CREATE** — implementation |

## WHAT — `CommandHistory` API

```python
class CommandHistory:
    """In-session command history with Up/Down navigation."""

    def add(self, text: str) -> None: ...
    def up(self, current_text: str) -> str | None: ...
    def down(self) -> str | None: ...
    def reset_cursor(self) -> None: ...
```

### Method Signatures & Behavior

- **`add(text: str) -> None`**
  - Strip whitespace; reject if empty after strip
  - Suppress if identical to last entry (consecutive duplicate)
  - Append to entries list
  - Call `reset_cursor()`

- **`up(current_text: str) -> str | None`**
  - If no entries, return `None`
  - On first call (cursor at end): save `current_text` as draft
  - If already at oldest entry (cursor == 0), return `None`
  - Decrement cursor, return `_entries[cursor]`

- **`down() -> str | None`**
  - If cursor is already past end (at draft position), return `None`
  - Increment cursor
  - If cursor == len(entries): return saved draft
  - Otherwise return `_entries[cursor]`

- **`reset_cursor() -> None`**
  - Set cursor to `len(_entries)` (past end)
  - Clear draft to `""`

## DATA — Internal State

```python
_entries: list[str]    # history entries in submission order
_cursor: int           # current navigation index; len(_entries) = "at draft"
_draft: str            # saved current input when entering history
```

## ALGORITHM — Core Logic (pseudocode)

```
add(text):
    text = text.strip()
    if not text: return
    if _entries and _entries[-1] == text: return
    _entries.append(text)
    reset_cursor()

up(current_text):
    if not _entries: return None
    if _cursor == len(_entries): _draft = current_text  # save draft on first Up
    if _cursor == 0: return None                        # at oldest
    _cursor -= 1
    return _entries[_cursor]

down():
    if _cursor >= len(_entries): return None             # already at draft
    _cursor += 1
    if _cursor == len(_entries): return _draft           # restore draft
    return _entries[_cursor]
```

## HOW — Integration Points

- No imports from Textual or any other module
- Pure Python, fully testable in isolation
- Place in `src/mcp_coder/icoder/core/command_history.py`

## Tests to Write (`tests/icoder/test_command_history.py`)

1. `test_up_empty_history_returns_none` — `up()` on fresh instance returns `None`
2. `test_down_empty_history_returns_none` — `down()` on fresh instance returns `None`
3. `test_add_and_up_returns_entry` — add one entry, `up()` returns it
4. `test_up_multiple_entries` — add A, B, C; `up()` returns C, B, A in order
5. `test_up_at_oldest_returns_none` — after navigating to oldest, next `up()` returns `None`
6. `test_down_restores_entries_then_draft` — navigate up fully, then `down()` walks forward, final `down()` returns draft
7. `test_down_at_newest_returns_none` — without navigating up, `down()` returns `None`
8. `test_draft_preservation` — type "draft text", up, then down past newest restores "draft text"
9. `test_duplicate_handling` — parameterized: `("consecutive", ["A", "A"], 1)` expects dedup; `("non_consecutive", ["A", "B", "A"], 3)` expects all stored
10. `test_blank_input_rejected` — parameterized over `"  "`, `"\t"`, `"\n"`, `""`: each is rejected by `add()`
11. `test_multiline_entry` — multi-line string stored and returned intact
12. `test_reset_cursor` — after navigating up, `reset_cursor()` puts cursor back at end
13. `test_add_resets_cursor` — navigating up then adding new entry resets position

## LLM Prompt

```
Implement Step 1 of issue #631 (iCoder command history).
See pr_info/steps/summary.md for full context and pr_info/steps/step_1.md for this step's spec.

TDD approach:
1. Create tests/icoder/test_command_history.py with all unit tests listed in step_1.md
2. Create src/mcp_coder/icoder/core/command_history.py implementing CommandHistory
3. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
4. Commit when all checks pass
```
