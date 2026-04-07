# Issue #628: iCoder Slash Command Autocomplete Dropdown

## Summary

Add a slash command autocomplete dropdown to the iCoder TUI. When the user types `/` as the first character, an `OptionList` widget appears above the input showing matching commands, filtering in real-time. Tab selects, Escape dismisses, Enter always submits (unchanged).

## Architecture / Design Changes

### Three-layer architecture preserved

All filter logic stays in `core/` as pure Python; the widget is a dumb view.

```
core/command_registry.py  ──► filter_by_input(input_text) → list[Command]
                                 (pure function, no Textual dependency)

ui/widgets/command_autocomplete.py  ──► thin OptionList wrapper
                                        show/hide/update_matches/CommandSelected message

ui/widgets/input_area.py  ──► owns autocomplete visibility tracking (~2 fields)
                               drives dropdown + emits EventLog transitions
                               forwards Up/Down/Tab/Escape when dropdown visible

ui/app.py  ──► composes CommandAutocomplete between OutputLog and InputArea
               wires CommandSelected → insert text into InputArea
```

### Key design decisions

| Topic | Decision |
|-------|----------|
| State machine class | **Not needed.** InputArea tracks `_ac_visible` + `_ac_matches` (2 fields) and emits events directly. The diff logic is ~15 lines — not enough to justify a separate class. |
| Filter location | `CommandRegistry.filter_by_input(raw_input)` — keeps the "starts with `/`" gate inside the registry |
| Trigger | `input_text.startswith("/")` only — no false positives on URLs/paths |
| Focus | InputArea always holds focus; dropdown never steals it |
| Key routing | Dropdown visible → Up/Down/Tab/Escape go to dropdown; hidden → all keys behave as today |
| Enter | Always submits, regardless of dropdown state |
| Empty matches | Show disabled `(no matching commands)` row (dropdown stays visible) |
| Events | Transition-based: `autocomplete_shown`, `autocomplete_filtered`, `autocomplete_selected`, `autocomplete_hidden(reason=...)` |

### Visibility invariant

**Dropdown visible ⟺ input text starts with `/`.**

Single rule, enforced in `on_text_area_changed`. No per-key state machine.

## Files Created or Modified

### New files
| File | Purpose |
|------|---------|
| `src/mcp_coder/icoder/ui/widgets/command_autocomplete.py` | Thin `OptionList` wrapper widget |
| `tests/icoder/test_autocomplete_pilot.py` | Pilot integration tests for autocomplete |

### Modified files
| File | Change |
|------|--------|
| `src/mcp_coder/icoder/core/command_registry.py` | Add `filter_by_input()` method |
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | Autocomplete state tracking, key routing, event emission |
| `src/mcp_coder/icoder/ui/app.py` | Compose `CommandAutocomplete`, pass registry/event_log to InputArea, wire `CommandSelected` |
| `src/mcp_coder/icoder/ui/styles.py` | CSS for `CommandAutocomplete` |
| `tests/icoder/test_command_registry.py` | Add `filter_by_input` unit tests |
| `tests/icoder/test_snapshots.py` | Add dropdown snapshot tests |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `filter_by_input()` to `CommandRegistry` (TDD: tests first) | `feat(icoder): add filter_by_input to CommandRegistry` |
| 2 | Create `CommandAutocomplete` widget (thin OptionList wrapper) | `feat(icoder): add CommandAutocomplete widget` |
| 3 | Wire autocomplete into InputArea and ICoderApp (visibility, key routing, events) | `feat(icoder): integrate autocomplete into InputArea and app` |
| 4 | Pilot integration tests for full autocomplete behavior | `test(icoder): add autocomplete pilot integration tests` |
| 5 | Snapshot tests for dropdown visual states | `test(icoder): add autocomplete snapshot tests` |
