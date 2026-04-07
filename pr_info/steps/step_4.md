# Step 4: Wire Autocomplete into `InputArea`

> **Context:** See `pr_info/steps/summary.md` and `Decisions.md` (D1, D2, D5).

## Goal

Make `InputArea` hold the current `AutocompleteState`, recompute on every text change, drive the `CommandAutocomplete` widget, route navigation keys when the dropdown is visible, and emit transition events.

## WHERE

| Action | File |
|--------|------|
| Modify | `src/mcp_coder/icoder/ui/widgets/input_area.py` |

## Imports to add

In `src/mcp_coder/icoder/ui/widgets/input_area.py`:

- `from ..core.autocomplete_state import compute_next_state, AutocompleteState`
- `from ..core.command_registry import CommandRegistry`
- `from ..core.event_log import EventLog`
- `from .command_autocomplete import CommandAutocomplete`
- `from textual.css.query import NoMatches`

## WHAT

```python
class InputArea(TextArea):
    def __init__(
        self,
        *args: Any,
        registry: CommandRegistry | None = None,
        event_log: EventLog | None = None,
        **kwargs: Any,
    ) -> None:
        """Accept optional registry and event_log for autocomplete.

        Both default to None for backward compatibility — existing tests that
        construct InputArea() with no args must keep working (constraint I7).
        """
        super().__init__(*args, **kwargs)
        self._registry: CommandRegistry | None = registry
        self._event_log: EventLog | None = event_log
        self._ac_state: AutocompleteState = AutocompleteState(
            visible=False, matches=(), highlighted_index=-1
        )
```

## HOW — `on_text_area_changed`

After the existing resize logic, append the autocomplete block:

```python
if self._registry is None:
    return

prev = self._ac_state
new = compute_next_state(self.text, self._registry)
self._ac_state = new

try:
    dropdown = self.screen.query_one(CommandAutocomplete)
except NoMatches:
    return  # dropdown not mounted yet (e.g. initial load) — skip silently

if new.visible:
    dropdown.update_matches(list(new.matches))
    dropdown.show_dropdown()
else:
    dropdown.hide_dropdown()

if self._event_log is not None:
    self._emit_ac_event(prev, new)
```

## HOW — `_emit_ac_event(prev, new)`

Maps the (prev, new) state diff to event log entries:

| prev.visible | new.visible | Condition | Event emitted |
|-------------|------------|-----------|---------------|
| False | True  | (always)                          | `autocomplete_shown` with `matches=[names]` |
| True  | True  | `prev.matches != new.matches`     | `autocomplete_filtered` with `query=text`, `matches=[names]` |
| True  | True  | `prev.matches == new.matches`     | (no event) |
| True  | False | (always)                          | `autocomplete_hidden` with `reason="prefix_removed"` |
| False | False | (always)                          | (no event) |

`autocomplete_selected` and `autocomplete_hidden(reason="escape"/"selected"/"submit")` are emitted from the key handler (below), not from `_emit_ac_event`.

## HOW — `_on_key` extensions (BEFORE existing handlers)

When `self._ac_state.visible` is True, intercept Escape / Up / Down / Tab / Enter:

```python
if self._ac_state.visible:
    dropdown = self.screen.query_one(CommandAutocomplete)

    if event.key == "escape":
        event.stop()
        event.prevent_default()
        dropdown.hide_dropdown()
        self._ac_state = AutocompleteState(visible=False, matches=(), highlighted_index=-1)
        if self._event_log is not None:
            self._event_log.emit("autocomplete_hidden", reason="escape")
            self._event_log.emit("autocomplete_key_routed", key="escape")
        return

    if event.key == "up":
        event.stop()
        event.prevent_default()
        dropdown.highlight_previous()
        if self._event_log is not None:
            self._event_log.emit("autocomplete_key_routed", key="up")
        return

    if event.key == "down":
        event.stop()
        event.prevent_default()
        dropdown.highlight_next()
        if self._event_log is not None:
            self._event_log.emit("autocomplete_key_routed", key="down")
        return

    if event.key == "tab":
        event.stop()
        event.prevent_default()
        name = dropdown.select_highlighted()
        if name:
            self.load_text(name + " ")
            self.move_cursor(self.document.end)
            if self._event_log is not None:
                self._event_log.emit("autocomplete_selected", command=name)
        dropdown.hide_dropdown()
        self._ac_state = AutocompleteState(visible=False, matches=(), highlighted_index=-1)
        if self._event_log is not None:
            self._event_log.emit("autocomplete_hidden", reason="selected")
            self._event_log.emit("autocomplete_key_routed", key="tab")
        return
```

### Enter branch — explicit

The dropdown-hide block below is inserted **inside** the existing `if event.key == "enter":` branch, BEFORE the existing `event.stop() / text = self.text.strip() / post_message / clear()` sequence. Do not create a new Enter handler — extend the existing one.

The existing Enter handler must hide the dropdown (if visible) but **always submit**:

```python
if event.key == "enter":
    if self._ac_state.visible:
        dropdown = self.screen.query_one(CommandAutocomplete)
        # Note: per Decision D2, Enter does NOT auto-select. It always submits.
        # The dropdown is hidden as a side effect of submission.
        dropdown.hide_dropdown()
        self._ac_state = AutocompleteState(visible=False, matches=(), highlighted_index=-1)
        if self._event_log is not None:
            self._event_log.emit("autocomplete_hidden", reason="submit")
    # ... existing Enter handling continues unchanged (submit the input)
```

**Important:** Use `self.load_text(name + " ")` + `self.move_cursor(self.document.end)` for Tab-insert — NOT `self.insert(...)`. This avoids the ambiguity around the `TextArea.insert()` signature.

## DATA

- `self._registry: CommandRegistry | None`
- `self._event_log: EventLog | None`
- `self._ac_state: AutocompleteState`

## Backward compatibility (constraint I7)

`InputArea()` (no args) must still work. Tests constructing `InputArea()` with no registry must mount and handle text changes without crashing.

Add a unit/pilot test enforcing this in `tests/icoder/test_widgets.py` (where the existing `InputArea` widget tests live):

```python
async def test_input_area_no_registry_backward_compat():
    """InputArea() with no registry mounts and accepts text changes (no autocomplete behavior)."""
```

## Commit

`feat(icoder): wire autocomplete into InputArea`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md (D1, D2, D5) for context, then implement Step 4.

1. Modify src/mcp_coder/icoder/ui/widgets/input_area.py:
   - Add registry, event_log kwargs to __init__ (both default None — I7).
   - Add self._ac_state: AutocompleteState field.
   - Extend on_text_area_changed to call compute_next_state, drive dropdown, emit events.
   - Implement _emit_ac_event(prev, new) per the table in step_4.md.
   - Extend _on_key to route Escape/Up/Down/Tab when self._ac_state.visible (BEFORE existing handlers).
   - Use load_text(name + " ") + move_cursor(self.document.end) for Tab-insert (NOT insert()).
   - Update Enter handler to hide dropdown on submit (still always submits).
2. Add backward-compat test that InputArea() with no args mounts cleanly.
3. Run all five quality checks — all must pass.
4. Commit: "feat(icoder): wire autocomplete into InputArea"
```
