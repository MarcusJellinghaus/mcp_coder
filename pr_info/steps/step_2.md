# Step 2: Create `CommandAutocomplete` Widget

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Create a thin `OptionList` wrapper widget that displays autocomplete suggestions. This is a dumb view — no business logic, no filtering, just show/hide/update what it's told to show.

## WHERE

| Action | File |
|--------|------|
| Create | `src/mcp_coder/icoder/ui/widgets/command_autocomplete.py` |
| Modify | `src/mcp_coder/icoder/ui/styles.py` |
| Create | `tests/icoder/test_command_autocomplete.py` |

## WHAT

```python
class CommandAutocomplete(Static):
    """Autocomplete dropdown for slash commands. Thin OptionList wrapper."""

    class CommandSelected(Message):
        """Posted when user Tab-selects a command."""
        def __init__(self, command_name: str) -> None: ...

    def compose(self) -> ComposeResult:
        """Yield an OptionList widget."""

    def update_matches(self, matches: list[Command]) -> None:
        """Replace option list contents with given matches.
        If matches is empty, show a single disabled '(no matching commands)' row."""

    def show_dropdown(self) -> None:
        """Make the dropdown visible (set display=True)."""

    def hide_dropdown(self) -> None:
        """Hide the dropdown (set display=False)."""

    @property
    def is_visible(self) -> bool:
        """Whether the dropdown is currently displayed."""

    def highlight_next(self) -> None:
        """Move highlight down one item in the OptionList."""

    def highlight_previous(self) -> None:
        """Move highlight up one item in the OptionList."""

    def select_highlighted(self) -> str | None:
        """Return the command name of the highlighted item, or None."""
```

## HOW

- `CommandAutocomplete` extends `Static` (container) and composes an `OptionList` inside
- Uses `self.display = True/False` for show/hide
- `OptionList` from `textual.widgets` provides highlight navigation out of the box
- `update_matches` calls `option_list.clear_options()` then adds new ones
- For empty matches, add a single `Option("(no matching commands)", disabled=True)`
- Each option's prompt shows `"/name — description"` format
- Store command names in option IDs for retrieval on select
- Hidden by default (CSS: `display: none`)

## ALGORITHM

```python
def update_matches(self, matches: list[Command]) -> None:
    option_list = self.query_one(OptionList)
    option_list.clear_options()
    if not matches:
        option_list.add_option(Option("(no matching commands)", disabled=True))
        return
    for cmd in matches:
        option_list.add_option(Option(f"{cmd.name} — {cmd.description}", id=cmd.name))
    option_list.highlighted = 0  # auto-highlight first item
```

## DATA

- `CommandSelected.command_name: str` — e.g. `"/help"`
- `update_matches` takes `list[Command]` from `core.types`
- `select_highlighted()` returns `str | None` — the command name string

## CSS Addition (styles.py)

```css
CommandAutocomplete {
    display: none;       /* hidden by default */
    height: auto;
    max-height: 8;       /* cap dropdown height */
    background: #2d2d2d;
    color: #d4d4d4;
}
```

## Tests

`tests/icoder/test_command_autocomplete.py` — widget tests using a minimal Textual app:

```python
@pytest.mark.textual_integration
async def test_dropdown_hidden_by_default():
    """CommandAutocomplete is not displayed initially."""

@pytest.mark.textual_integration
async def test_show_hide():
    """show_dropdown/hide_dropdown toggle display."""

@pytest.mark.textual_integration
async def test_update_matches_shows_commands():
    """update_matches populates the OptionList with command entries."""

@pytest.mark.textual_integration
async def test_update_matches_empty_shows_no_matching():
    """Empty matches list shows '(no matching commands)' disabled row."""

@pytest.mark.textual_integration
async def test_select_highlighted_returns_command_name():
    """select_highlighted returns the command name of the highlighted option."""

@pytest.mark.textual_integration
async def test_highlight_navigation():
    """highlight_next/highlight_previous cycle through options."""
```

## Commit

`feat(icoder): add CommandAutocomplete widget`

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement Step 2.

1. Create tests/icoder/test_command_autocomplete.py with the widget tests listed in step_2.md
2. Create src/mcp_coder/icoder/ui/widgets/command_autocomplete.py with the CommandAutocomplete widget
3. Add CSS for CommandAutocomplete to src/mcp_coder/icoder/ui/styles.py
4. Run all three quality checks (pylint, pytest, mypy) — all must pass
5. Commit: "feat(icoder): add CommandAutocomplete widget"
```
