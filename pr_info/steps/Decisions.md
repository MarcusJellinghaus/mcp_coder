# Design Decisions — Issue #628 Slash Command Autocomplete

Resolved decisions from plan-review discussion. Each entry is one line of rationale.

## D1. Transition state representation

**Decision:** Use a frozen dataclass `AutocompleteState` plus a pure function `compute_next_state(input_text: str, registry: CommandRegistry) -> AutocompleteState` in a new module `core/autocomplete_state.py`.

**Rationale:** Satisfies the issue's "unit-testable without Textual pilot" and "three-layer architecture" constraints with minimal ceremony. The caller diffs the previous and new state to emit transition events. Chosen over a mutable class mirroring `CommandHistory` because state is recomputed per keystroke (not accumulated).

## D2. `CommandSelected` Message — DROPPED

**Decision:** Do not introduce a `CommandAutocomplete.CommandSelected` Textual `Message`. `InputArea` handles Tab-select inline by calling `dropdown.select_highlighted()` and inserting text directly.

**Rationale:** KISS. The message would add a layer with no observer — `ICoderApp` would only forward it back to `InputArea`.

## D3. `CommandAutocomplete` base class

**Decision:** `CommandAutocomplete` extends `OptionList` directly. No `Static` wrapper, no inner `compose()`.

**Rationale:** KISS. The wrapper layer was delegating every method to the inner `OptionList`.

## D4. `AppCore` access from `ICoderApp`

**Decision:** Add public read-only properties `AppCore.registry` and `AppCore.event_log` (one-line `@property` each).

**Rationale:** Avoids reaching into `_core._registry` / `_core._event_log` from `ICoderApp`. Keeps the public API explicit.

## D5. Tab-insert format

**Decision:** Tab-selection inserts `"/help "` (command name + trailing space).

**Rationale:** Standard autocomplete UX — saves a keystroke for commands that take arguments.

## Round 2 plan corrections

- **C1 (blocker):** `EventLog` exposes `emit(event, **data)`, not `log(...)`. Step 4 pseudocode updated to call `self._event_log.emit(...)` everywhere.
- **S1:** Tests use the flat `tests/icoder/` layout — moved `test_autocomplete_state.py` out of the non-existent `tests/icoder/core/` subdirectory.
- **S2:** Step 4 now lists the explicit imports to add to `input_area.py` (`compute_next_state`, `AutocompleteState`, `CommandRegistry`, `EventLog`, `CommandAutocomplete`, `NoMatches`).
- **S3:** Step 4 Enter branch clarified — the dropdown-hide block lives **inside** the existing `if event.key == "enter":` branch, before the existing submit sequence.
- **S4:** Backward-compat `InputArea()` test goes in the existing `tests/icoder/test_widgets.py` file.
- **S5:** `autocomplete_key_routed(key=...)` added to the events row in `summary.md`.
- **S6:** Step 6 LLM prompt now starts with a one-line check that the `textual_integration` marker is registered in `pyproject.toml`.
