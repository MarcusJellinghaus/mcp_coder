# iCoder: Command History (Up/Down Arrow) — Issue #631

## Summary

Add in-session command history to the iCoder TUI so that Up/Down arrow keys cycle through previously submitted inputs. This provides a natural "retry after error" UX.

## Architecture & Design Changes

### New Module

- **`src/mcp_coder/icoder/core/command_history.py`** — Pure Python `CommandHistory` class (no Textual dependency), following the existing `core/` pattern where domain logic lives free of UI imports (like `AppCore`, `CommandRegistry`).

### Modified Modules

- **`src/mcp_coder/icoder/ui/widgets/input_area.py`** — `InputArea` owns a `CommandHistory` instance. `_on_key()` gains two `elif` branches for Up/Down arrow interception with boundary-line detection.
- **`src/mcp_coder/icoder/ui/app.py`** — `on_input_area_input_submitted()` calls `history.add(text)` on the `InputArea`'s history instance.

### New Test Files

- **`tests/icoder/test_command_history.py`** — Pure Python unit tests for `CommandHistory` API.
- **`tests/icoder/test_widgets.py`** — Additional async Textual tests for Up/Down key integration (appended to existing file).

## Design Decisions (from issue)

| Decision | Choice |
|----------|--------|
| History state location | `CommandHistory` in `core/` (pure Python) |
| Up/Down behavior | Boundary-line detection: Up on first line = history back, Down on last line = history forward |
| Duplicate suppression | Consecutive duplicates suppressed |
| Whitespace-only inputs | Rejected in `add()` |
| Draft preservation | Save current text on first Up; restore when navigating past newest |
| Multi-line entries | Stored and restored fully |
| Max history size | No cap (in-memory, single session) |
| Slash commands | Included in history |

## Ownership Model

`InputArea` creates and owns its `CommandHistory` — no DI injection needed since `CommandHistory` is a stateless, dependency-free object. The app layer simply calls `input_area.history.add(text)` on submit.

## Files to Create or Modify

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/core/command_history.py` | **CREATE** |
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | **MODIFY** |
| `src/mcp_coder/icoder/ui/app.py` | **MODIFY** |
| `tests/icoder/test_command_history.py` | **CREATE** |
| `tests/icoder/test_widgets.py` | **MODIFY** |

## Implementation Steps

1. **Step 1** — `CommandHistory` class + unit tests
2. **Step 2** — `InputArea` Up/Down integration + widget key tests
3. **Step 3** — Wire `history.add()` in `ICoderApp` submit handler
