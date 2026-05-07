"""SessionPickerScreen — modal session picker for prior icoder logs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from textual.app import App, ComposeResult
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


class _StartupPickerApp(App[Optional[Path]]):
    """Tiny App that hosts a single SessionPickerScreen at startup."""

    def __init__(self, summaries: list[LogSummary]) -> None:
        super().__init__()
        self._summaries = summaries

    def on_mount(self) -> None:
        """Push the picker; its dismissed value becomes the App's exit value."""

        def _on_pick(value: Optional[Path]) -> None:
            self.exit(value)

        self.push_screen(SessionPickerScreen(self._summaries), _on_pick)


def run_startup_picker(
    summaries: list[LogSummary],
    *,
    app_factory: Optional[Callable[[list[LogSummary]], App[Optional[Path]]]] = None,
) -> Optional[Path]:
    """Run a tiny modal picker app and return the user's selection.

    Used by the icoder CLI to show a session picker synchronously before
    the main TUI starts. Esc returns ``None``.

    Args:
        summaries: Log summaries to display.
        app_factory: Optional override that returns the App to run; tests
            substitute a deterministic factory to avoid driving real TUI.
    """
    factory = app_factory or _StartupPickerApp
    app = factory(summaries)
    return app.run()
