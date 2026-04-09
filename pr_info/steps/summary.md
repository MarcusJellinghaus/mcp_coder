# Issue #754 — icoder: `\` + Enter as newline escape

## Problem

Shift+Enter doesn't insert a newline in icoder on Windows. The terminal sends `\r` for both Enter and Shift+Enter, so Textual can't distinguish them.

## Solution

`\` + Enter as a newline escape mechanism, with a status hint and documentation.

## Architectural / Design Changes

### Modified modules

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | Backslash+Enter newline logic in `_on_key` Enter handler |
| `src/mcp_coder/icoder/ui/app.py` | Add `Static` hint widget below `InputArea`; toggle visibility on text changes |
| `src/mcp_coder/icoder/ui/styles.py` | CSS for `#input-hint` (right-aligned, same background); remove `InputArea` default border |
| `src/mcp_coder/icoder/core/commands/help.py` | Add "Keyboard shortcuts" section to `/help` output |

### New files

| File | Purpose |
|------|---------|
| `docs/iCoder.md` | User guide: startup, commands, autocomplete, streaming, keyboard shortcuts, `\` escape |

### Modified test files

| File | Change |
|------|--------|
| `tests/icoder/test_widgets.py` | Parametrized backslash+Enter tests |
| `tests/icoder/test_app_pilot.py` | Hint widget visibility tests |
| `tests/icoder/test_snapshots.py` | Snapshot updates (new hint widget in layout) |
| `tests/icoder/test_command_registry.py` or `tests/icoder/test_app_core.py` | `/help` output assertion |

### Design decisions

1. **No new widget class** — the hint is a plain `Static` with an id, toggled by CSS class
2. **No new messages/watchers** — `ICoderApp` listens to `TextArea.Changed` (already emitted by Textual) to toggle hint visibility
3. **Backslash logic lives in `InputArea._on_key`** — slots in after autocomplete dismissal, before submit, using raw `self.text` (not `.strip()`)
4. **Parity-based** — odd trailing `\` count → newline; even → submit (always strips one `\`)
5. **Shift+Enter preserved** — existing code stays as fallback

## Implementation Steps

1. **Step 1** — Backslash+Enter newline logic + tests
2. **Step 2** — Status hint widget + visibility toggling + tests
3. **Step 3** — `/help` keyboard shortcuts section + tests
4. **Step 4** — `docs/iCoder.md` user guide
5. **Step 5** — Snapshot updates
