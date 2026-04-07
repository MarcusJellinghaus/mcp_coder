# Step 5: Wire `CommandAutocomplete` into `ICoderApp` + `AppCore` Properties

> **Context:** See `pr_info/steps/summary.md` and `Decisions.md` (D4).

## Goal

Compose the `CommandAutocomplete` widget in the app, pass `registry` and `event_log` from `AppCore` into `InputArea` via new public properties (Decision D4 — avoids private-attribute access).

## WHERE

| Action | File |
|--------|------|
| Modify | `src/mcp_coder/icoder/core/app_core.py` |
| Modify | `src/mcp_coder/icoder/ui/app.py` |

## WHAT — `AppCore` public properties (D4)

```python
class AppCore:
    @property
    def registry(self) -> CommandRegistry:
        """Public read-only access to the command registry."""
        return self._registry

    @property
    def event_log(self) -> EventLog:
        """Public read-only access to the event log."""
        return self._event_log
```

One-line `@property` each — no setters, no logic.

## WHAT — `ICoderApp.compose()`

```python
def compose(self) -> ComposeResult:
    yield OutputLog()
    yield CommandAutocomplete()  # NEW: between OutputLog and InputArea
    yield InputArea(
        registry=self._core.registry,
        event_log=self._core.event_log,
    )
```

`CommandAutocomplete` is yielded **above** `InputArea` per the issue's UX sketch (dropdown appears above the input). The CSS from Step 2 keeps it `display: none` until `show_dropdown()` is called.

No `on_command_autocomplete_command_selected` handler — Decision D2 dropped the `CommandSelected` Message; `InputArea` handles Tab-select inline (Step 4).

## HOW

- `AppCore` already constructs a default `CommandRegistry` and `EventLog` in `__init__`. The properties simply expose them.
- `ICoderApp(app_core)` constructor signature is unchanged — backward compat preserved.
- The widget is queryable via `self.screen.query_one(CommandAutocomplete)` from `InputArea` (Step 4 already does this).

## DATA

- `AppCore.registry: CommandRegistry`
- `AppCore.event_log: EventLog`

## Backward compatibility

- `ICoderApp(app_core)` still works because `AppCore` always provides the defaults.
- Existing snapshot/pilot tests that construct `ICoderApp(app_core)` without changes must keep passing. Step 7 (snapshot tests) explicitly verifies this.

## Commit

`feat(icoder): integrate autocomplete into ICoderApp`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md (D4) for context, then implement Step 5.

1. Modify src/mcp_coder/icoder/core/app_core.py:
   - Add public @property registry returning self._registry.
   - Add public @property event_log returning self._event_log.
2. Modify src/mcp_coder/icoder/ui/app.py:
   - Import CommandAutocomplete.
   - Yield CommandAutocomplete() in compose() above InputArea.
   - Construct InputArea(registry=self._core.registry, event_log=self._core.event_log).
3. Run all five quality checks — all must pass. Existing pilot/snapshot tests must keep passing.
4. Commit: "feat(icoder): integrate autocomplete into ICoderApp"
```
