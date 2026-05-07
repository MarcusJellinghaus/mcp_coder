"""SessionPickerScreen — modal session picker for prior icoder logs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static

from mcp_coder.icoder.core.types import LogSummary


def format_picker_row(summary: LogSummary) -> str:
    """Format a LogSummary as a single picker row."""
    when = summary.timestamp.strftime("%Y-%m-%d %H:%M")
    prov = summary.provider or "?"
    return f'{when} · {prov} · {summary.n_turns} turns · "{summary.first_prompt}"'


class SessionPickerScreen(ModalScreen[Optional[Path]]):
    """Modal session picker. Returns the selected log Path, or None on Esc."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, summaries: list[LogSummary]) -> None:
        """Initialise with the list of log summaries to display.

        Args:
            summaries: Summaries to render as picker rows, newest first.
        """
        super().__init__()
        self._summaries = summaries

    def compose(self) -> ComposeResult:
        """Compose the picker layout.

        Yields:
            Container with a header and an OptionList of rows.
        """
        yield Container(
            Static(
                "Select a session — Up/Down to move, Enter to select, Esc to cancel"
            ),
            OptionList(*[format_picker_row(s) for s in self._summaries]),
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Dismiss the screen with the path of the selected summary."""
        self.dismiss(self._summaries[event.option_index].path)

    def action_cancel(self) -> None:
        """Dismiss the screen with no selection (Esc binding)."""
        self.dismiss(None)
