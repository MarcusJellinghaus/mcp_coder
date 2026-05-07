# Step 9 — `SessionPickerScreen` (ModalScreen + OptionList)

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_9.md`) with strict TDD. Tests first (use Textual
> `Pilot` and the `textual_integration` marker), then implementation.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Create: `src/mcp_coder/icoder/ui/widgets/session_picker.py`
- Create tests: `tests/icoder/test_session_picker.py`
  (`@pytest.mark.textual_integration`)

## WHAT

```python
class SessionPickerScreen(ModalScreen[Optional[Path]]):
    """Modal session picker. Returns the selected log Path, or None on Esc."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, summaries: list[LogSummary]) -> None: ...

    def compose(self) -> ComposeResult:
        # OptionList of formatted rows
        ...

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None: ...

    def action_cancel(self) -> None: ...
```

Helper (also in this file):

```python
def format_picker_row(summary: LogSummary) -> str:
    """<YYYY-MM-DD HH:MM> · <provider> · <N turns> · "<first prompt>" """
```

## HOW

- Use Textual's stock `OptionList` widget — gives Up/Down/Enter for free.
- Wrap in `ModalScreen[Optional[Path]]` so callers can `await
  app.push_screen(SessionPickerScreen(summaries))` and get the path back.
- `Esc` → `self.dismiss(None)`.
- Enter on an option → `self.dismiss(summaries[index].path)`.
- The screen handles only the selection mechanic; opening it (at startup
  or via `/load`) is Step 10 / Step 11.

## ALGORITHM

```
compose():
    yield Container(
        Static("Select a session — Up/Down to move, Enter to select, Esc to cancel"),
        OptionList(*[format_picker_row(s) for s in self._summaries]),
    )

on_option_list_option_selected(event):
    self.dismiss(self._summaries[event.option_index].path)

format_picker_row(s):
    when = s.timestamp.strftime("%Y-%m-%d %H:%M")
    prov = s.provider or "?"
    return f'{when} · {prov} · {s.n_turns} turns · "{s.first_prompt}"'
```

## DATA

- Screen result: `Optional[Path]`.
- Row strings: `"YYYY-MM-DD HH:MM · <provider> · <N> turns · "<prompt>""`.

## Test Cases

(All `textual_integration`.)

1. Render with two summaries; assert both rows visible in the
   `OptionList` (via widget query).
2. Press Down then Enter → screen dismisses with `summaries[1].path`.
3. Press Esc → screen dismisses with `None`.
4. `format_picker_row` unit tests (pure function, no Textual):
   - typical row formatting,
   - missing provider → `"?"`,
   - 80-char prompt rendered as-is (no further truncation here).
5. Empty `summaries` list → `OptionList` is empty; Esc still dismisses
   with `None`. (Caller decides not to show the picker when the list is
   empty; this is a defensive guard.)

## Out of Scope

- Mounting the picker — Step 10 (`/load`) and Step 11 (startup).
- Disk scanning — Step 7.
