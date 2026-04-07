# Step 2: Create `CommandAutocomplete` Widget

> **Context:** See `pr_info/steps/summary.md` for full issue context. See `Decisions.md` D3 for the base-class choice.

## Goal

Create the autocomplete dropdown widget by **extending `OptionList` directly** (Decision D3 — no `Static` wrapper, no inner `compose()`). This is a dumb view: no filter logic, no transition tracking — just show/hide and update what it's told to show.

## WHERE

| Action | File |
|--------|------|
| Create | `src/mcp_coder/icoder/ui/widgets/command_autocomplete.py` |
| Modify | `src/mcp_coder/icoder/ui/styles.py` |
| Create | `tests/icoder/test_command_autocomplete.py` |

## WHAT

```python
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from mcp_coder.icoder.core.types import Command


class CommandAutocomplete(OptionList):
    """Autocomplete dropdown for slash commands. Subclass of OptionList."""

    def update_matches(self, matches: list[Command]) -> None:
        """Replace option list contents with given matches.

        If `matches` is empty, show a single disabled '(no matching commands)' row.
        """

    def show_dropdown(self) -> None:
        """Make the dropdown visible (set display=True)."""

    def hide_dropdown(self) -> None:
        """Hide the dropdown (set display=False)."""

    @property
    def is_visible(self) -> bool:
        """Whether the dropdown is currently displayed."""

    def highlight_next(self) -> None:
        """Move highlight down one item."""

    def highlight_previous(self) -> None:
        """Move highlight up one item."""

    def select_highlighted(self) -> str | None:
        """Return the command name (option id) of the highlighted item, or None."""
```

**No `CommandSelected` Message class** (Decision D2 — dropped).

## HOW

- `CommandAutocomplete` IS an `OptionList` — no inner widget, no `compose()`.
- Uses `self.display = True/False` for show/hide.
- `OptionList` provides highlight/navigation methods natively; `highlight_next`/`highlight_previous` are thin wrappers (or just call the inherited `action_cursor_down` / `action_cursor_up`).
- `update_matches` calls `self.clear_options()` then adds new ones.
- For empty matches, add a single `Option("(no matching commands)", disabled=True)`.
- Each option: prompt is `f"{cmd.name} — {cmd.description}"`, `id` is `cmd.name`.
- Hidden by default (CSS `display: none`).
- `select_highlighted()` returns `self.get_option_at_index(self.highlighted).id` (or `None` if no highlight or disabled row).

## ALGORITHM

```python
def update_matches(self, matches: list[Command]) -> None:
    self.clear_options()
    if not matches:
        self.add_option(Option("(no matching commands)", disabled=True))
        return
    for cmd in matches:
        self.add_option(Option(f"{cmd.name} — {cmd.description}", id=cmd.name))
    self.highlighted = 0  # auto-highlight first item
```

## DATA

- `update_matches` takes `list[Command]` from `core.types`.
- `select_highlighted()` returns `str | None` — the command name string (option id).

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

`tests/icoder/test_command_autocomplete.py` — widget tests using a minimal Textual app harness. Note: since `CommandAutocomplete` IS an `OptionList`, queries use `query_one(CommandAutocomplete)` directly — no inner `query_one(OptionList)`.

```python
pytestmark = pytest.mark.textual_integration

async def test_dropdown_hidden_by_default():
    """CommandAutocomplete is not displayed initially (display=False)."""

async def test_show_hide_toggles_display():
    """show_dropdown/hide_dropdown toggle display + is_visible reflects it."""

async def test_update_matches_shows_commands():
    """update_matches populates options with '/name — description' labels and id=name."""

async def test_update_matches_empty_shows_no_matching():
    """Empty matches list shows a single disabled '(no matching commands)' row."""

async def test_select_highlighted_returns_command_name():
    """select_highlighted returns the option id (command name) of the highlighted row."""

async def test_highlight_navigation():
    """highlight_next / highlight_previous move the highlight through the options."""
```

No `CommandSelected` assertions (Decision D2 — message class dropped).

## Commit

`feat(icoder): add CommandAutocomplete widget`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md for context, then implement Step 2.

1. Create tests/icoder/test_command_autocomplete.py with the 6 widget tests listed above.
2. Create src/mcp_coder/icoder/ui/widgets/command_autocomplete.py with CommandAutocomplete extending OptionList directly.
3. Add CSS for CommandAutocomplete to src/mcp_coder/icoder/ui/styles.py.
4. Run all five quality checks — all must pass.
5. Commit: "feat(icoder): add CommandAutocomplete widget"
```
