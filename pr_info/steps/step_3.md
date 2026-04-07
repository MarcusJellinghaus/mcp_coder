# Step 3: Wire Autocomplete into InputArea and ICoderApp

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Integrate the autocomplete dropdown into the app. InputArea drives visibility and event emission. ICoderApp composes the widget and wires the selection message.

## WHERE

| Action | File |
|--------|------|
| Modify | `src/mcp_coder/icoder/ui/widgets/input_area.py` |
| Modify | `src/mcp_coder/icoder/ui/app.py` |

## WHAT — InputArea Changes

```python
class InputArea(TextArea):
    def __init__(
        self,
        registry: CommandRegistry | None = None,
        event_log: EventLog | None = None,
        **kwargs: Any,
    ) -> None:
        """Accept optional registry and event_log for autocomplete."""
        # New fields for autocomplete tracking:
        # self._ac_visible: bool = False
        # self._ac_matches: list[Command] = []
        # self._registry: CommandRegistry | None = registry
        # self._event_log: EventLog | None = event_log

    def on_text_area_changed(self) -> None:
        """Extended: drive autocomplete dropdown + emit transition events."""

    async def _on_key(self, event: events.Key) -> None:
        """Extended: forward Up/Down/Tab/Escape to dropdown when visible."""
```

## WHAT — ICoderApp Changes

```python
class ICoderApp(App[None]):
    def compose(self) -> ComposeResult:
        yield OutputLog()
        yield CommandAutocomplete()   # NEW: between OutputLog and InputArea
        yield InputArea(
            registry=self._core._registry,
            event_log=self._core._event_log,
        )

    def on_command_autocomplete_command_selected(
        self, message: CommandAutocomplete.CommandSelected
    ) -> None:
        """Insert selected command into InputArea, hide dropdown."""
```

## HOW — InputArea autocomplete integration

InputArea gets the `CommandAutocomplete` sibling via `self.screen.query_one(CommandAutocomplete)`.

### `on_text_area_changed` additions (after existing resize logic):

```python
# Autocomplete logic
if self._registry is None:
    return
dropdown = self.screen.query_one(CommandAutocomplete)
matches = self._registry.filter_by_input(self.text)
should_show = self.text.startswith("/")

if should_show and not self._ac_visible:
    # hidden → visible
    dropdown.update_matches(matches)
    dropdown.show_dropdown()
    self._ac_visible = True
    self._ac_matches = matches
    self._emit_ac_event("autocomplete_shown", matches=_names(matches))
elif should_show and matches != self._ac_matches:
    # still visible, matches changed
    dropdown.update_matches(matches)
    self._ac_matches = matches
    self._emit_ac_event("autocomplete_filtered", query=self.text, matches=_names(matches))
elif not should_show and self._ac_visible:
    # visible → hidden
    dropdown.hide_dropdown()
    self._ac_visible = False
    self._ac_matches = []
    self._emit_ac_event("autocomplete_hidden", reason="prefix_removed")
```

### `_on_key` additions (BEFORE existing Enter/Up/Down logic):

```python
# When dropdown visible, intercept navigation keys
if self._ac_visible:
    dropdown = self.screen.query_one(CommandAutocomplete)
    if event.key == "escape":
        event.stop()
        event.prevent_default()
        dropdown.hide_dropdown()
        self._ac_visible = False
        self._ac_matches = []
        self._emit_ac_event("autocomplete_hidden", reason="escape")
        return
    if event.key == "up":
        event.stop()
        event.prevent_default()
        dropdown.highlight_previous()
        return
    if event.key == "down":
        event.stop()
        event.prevent_default()
        dropdown.highlight_next()
        return
    if event.key == "tab":
        event.stop()
        event.prevent_default()
        name = dropdown.select_highlighted()
        if name:
            self.clear()
            self.insert(name + " ")
            self._emit_ac_event("autocomplete_selected", command=name)
        dropdown.hide_dropdown()
        self._ac_visible = False
        self._ac_matches = []
        self._emit_ac_event("autocomplete_hidden", reason="selected")
        return

# Existing Enter handling — UNCHANGED
if event.key == "enter":
    ...  # existing submit logic
    # Add: hide dropdown on submit if visible
    if self._ac_visible:
        dropdown.hide_dropdown()
        self._ac_visible = False
        self._ac_matches = []
        self._emit_ac_event("autocomplete_hidden", reason="submit")
```

## HOW — ICoderApp `CommandSelected` handler

```python
def on_command_autocomplete_command_selected(
    self, message: CommandAutocomplete.CommandSelected
) -> None:
    input_area = self.query_one(InputArea)
    input_area.clear()
    input_area.insert(message.command_name + " ")
```

Note: The `CommandSelected` message is posted by `CommandAutocomplete` but in the simplified approach, `InputArea` handles Tab directly (calling `select_highlighted()` and inserting text itself). The `CommandSelected` message may not be needed if `InputArea` handles everything. **Decide at implementation time:** if `InputArea` does the insertion directly in `_on_key`, the `CommandSelected` message on the widget becomes unused and can be omitted. Keep it simple.

## DATA

- `self._ac_visible: bool` — current dropdown visibility
- `self._ac_matches: list[Command]` — current match set (for change detection)
- `self._registry: CommandRegistry | None` — injected registry
- `self._event_log: EventLog | None` — injected event log

## Important: Backward Compatibility

- `InputArea` must still work without `registry`/`event_log` (both `None`). Existing tests create `InputArea()` with no args — they must not break.
- When `registry is None`, `on_text_area_changed` skips autocomplete logic entirely.
- All existing `InputArea` and `ICoderApp` tests must continue to pass without modification. If any existing test constructs `InputArea()` or `ICoderApp(app_core)` without the new params, it must work as before.

## Commit

`feat(icoder): integrate autocomplete into InputArea and app`

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement Step 3.

1. Modify src/mcp_coder/icoder/ui/widgets/input_area.py:
   - Add registry and event_log optional params to __init__
   - Add _ac_visible, _ac_matches tracking fields
   - Extend on_text_area_changed with autocomplete logic
   - Extend _on_key with dropdown key routing (before existing handlers)
   - Add _emit_ac_event helper method
2. Modify src/mcp_coder/icoder/ui/app.py:
   - Import CommandAutocomplete
   - Add it to compose() between OutputLog and InputArea
   - Pass registry and event_log to InputArea constructor
   - Access registry and event_log from self._core (add properties to AppCore if needed)
3. Run all three quality checks (pylint, pytest, mypy) — all must pass
4. Verify existing tests still pass unchanged
5. Commit: "feat(icoder): integrate autocomplete into InputArea and app"
```
