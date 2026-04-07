# Issue #628: iCoder Slash Command Autocomplete Dropdown

## Summary

Add a slash command autocomplete dropdown to the iCoder TUI. When the user types `/` as the first character, an `OptionList`-based widget appears above the input showing matching commands, filtering in real-time. Tab selects, Escape dismisses, Enter always submits (unchanged).

See `Decisions.md` for the resolved design decisions referenced below.

## Architecture / Design Changes

### Three-layer architecture preserved

All filter logic stays in `core/` as pure Python; the widget is a dumb view. State transitions are computed by a pure module that the UI layer calls.

```
core/command_registry.py     ──► filter_by_input(input_text) → list[Command]
                                   (pure, no Textual dependency)

core/autocomplete_state.py   ──► AutocompleteState (frozen dataclass)
                                   compute_next_state(text, registry) → AutocompleteState
                                   (pure, no Textual dependency)

ui/widgets/command_autocomplete.py
                             ──► extends OptionList directly
                                   show/hide/update_matches/highlight_*/select_highlighted

ui/widgets/input_area.py     ──► holds current AutocompleteState
                                   recomputes on text-changed, drives dropdown
                                   diffs prev vs new state to emit EventLog transitions
                                   forwards Up/Down/Tab/Escape when dropdown visible
                                   handles Tab-insert inline (no Message round-trip)

ui/app.py                    ──► composes CommandAutocomplete above InputArea
                                   constructs InputArea(registry=core.registry,
                                                        event_log=core.event_log)

core/app_core.py             ──► public properties: registry, event_log
```

### Key design decisions (see `Decisions.md` for full rationale)

| ID | Topic | Decision |
|----|-------|----------|
| D1 | State representation | Frozen `AutocompleteState` dataclass + pure `compute_next_state()` in `core/autocomplete_state.py`. Caller diffs prev vs new to emit events. |
| D2 | `CommandSelected` Message | **Dropped.** `InputArea` handles Tab-select inline. KISS — no observer for the message. |
| D3 | `CommandAutocomplete` base class | Extends `OptionList` **directly** (no `Static` wrapper). KISS. |
| D4 | `AppCore` access | Add public read-only properties `AppCore.registry` and `AppCore.event_log`. Avoids private-attribute access from `ICoderApp`. |
| D5 | Tab-insert format | `"/help "` (with trailing space). Standard autocomplete UX. |
| -- | Filter location | `CommandRegistry.filter_by_input(raw_input)` — keeps the "starts with `/`" gate inside the registry. |
| -- | Trigger | `input_text.startswith("/")` only — no false positives on URLs/paths. |
| -- | Focus | InputArea always holds focus; dropdown never steals it. |
| -- | Key routing | Dropdown visible → Up/Down/Tab/Escape go to dropdown; hidden → all keys behave as today. |
| -- | Enter | Always submits, regardless of dropdown state. |
| -- | Empty matches | Show disabled `(no matching commands)` row (dropdown stays visible). |
| -- | Events | Transition-based: `autocomplete_shown`, `autocomplete_filtered`, `autocomplete_selected`, `autocomplete_hidden(reason=...)`, `autocomplete_key_routed(key=...)`. |

### Visibility invariant

**Dropdown visible ⟺ input text starts with `/`.**

Single rule, enforced by `compute_next_state()`. No per-key state machine.

## Files Created or Modified

### New files
| File | Purpose |
|------|---------|
| `src/mcp_coder/icoder/core/autocomplete_state.py` | Frozen `AutocompleteState` + pure `compute_next_state()` |
| `src/mcp_coder/icoder/ui/widgets/command_autocomplete.py` | `OptionList` subclass for the dropdown |
| `tests/icoder/test_autocomplete_state.py` | Pure unit tests (no Textual) for state module |
| `tests/icoder/test_command_autocomplete.py` | Widget tests under `textual_integration` marker |
| `tests/icoder/test_autocomplete_pilot.py` | Pilot integration tests for full autocomplete behavior |

### Modified files
| File | Change |
|------|--------|
| `src/mcp_coder/icoder/core/command_registry.py` | Add `filter_by_input()` method |
| `src/mcp_coder/icoder/core/app_core.py` | Add public `registry` and `event_log` properties |
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | Hold `AutocompleteState`, drive dropdown, route keys, emit events |
| `src/mcp_coder/icoder/ui/app.py` | Compose `CommandAutocomplete`, pass registry/event_log into InputArea |
| `src/mcp_coder/icoder/ui/styles.py` | CSS for `CommandAutocomplete` |
| `tests/icoder/test_command_registry.py` | Add `filter_by_input` unit tests |
| `tests/icoder/test_snapshots.py` | Add dropdown snapshot tests; verify existing fixture still works |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `filter_by_input()` to `CommandRegistry` (TDD) | `feat(icoder): add filter_by_input to CommandRegistry` |
| 2 | Create `CommandAutocomplete` widget (extends `OptionList`) | `feat(icoder): add CommandAutocomplete widget` |
| 3 | Create `core/autocomplete_state.py` (pure state module) + unit tests | `feat(icoder): add autocomplete state module` |
| 4 | Wire autocomplete into `InputArea` (state + key routing + events) | `feat(icoder): wire autocomplete into InputArea` |
| 5 | Wire `CommandAutocomplete` into `ICoderApp` + `AppCore` properties | `feat(icoder): integrate autocomplete into ICoderApp` |
| 6 | Pilot integration tests for full autocomplete behavior | `test(icoder): add autocomplete pilot integration tests` |
| 7 | Snapshot tests for dropdown visual states | `test(icoder): add autocomplete snapshot tests` |
