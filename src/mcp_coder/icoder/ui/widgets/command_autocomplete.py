"""CommandAutocomplete widget — OptionList-based dropdown for slash commands."""

from __future__ import annotations

from textual.widgets import OptionList
from textual.widgets.option_list import Option

from mcp_coder.icoder.core.types import Command


class CommandAutocomplete(OptionList):
    """Autocomplete dropdown for slash commands. Subclass of OptionList."""

    def update_matches(self, matches: list[Command]) -> None:
        """Replace option list contents with given matches.

        If ``matches`` is empty, show a single disabled
        '(no matching commands)' row.
        """
        self.clear_options()
        if not matches:
            self.add_option(Option("(no matching commands)", disabled=True))
            return
        for cmd in matches:
            self.add_option(Option(f"{cmd.name} — {cmd.description}", id=cmd.name))
        self.highlighted = 0

    def show_dropdown(self) -> None:
        """Make the dropdown visible."""
        self.display = True

    def hide_dropdown(self) -> None:
        """Hide the dropdown."""
        self.display = False

    @property
    def is_visible(self) -> bool:
        """Whether the dropdown is currently displayed."""
        return bool(self.display)

    def highlight_next(self) -> None:
        """Move highlight down one item."""
        self.action_cursor_down()

    def highlight_previous(self) -> None:
        """Move highlight up one item."""
        self.action_cursor_up()

    def select_highlighted(self) -> str | None:
        """Return the command name (option id) of the highlighted item, or None."""
        if self.highlighted is None:
            return None
        if self.highlighted < 0 or self.highlighted >= self.option_count:
            return None
        option = self.get_option_at_index(self.highlighted)
        if option.disabled:
            return None
        return option.id
