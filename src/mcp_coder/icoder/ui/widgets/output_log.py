"""OutputLog widget — scrollable output area for conversation display."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import RichLog


class OutputLog(RichLog):
    """Scrollable output area for conversation display."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with internal line buffer for testability."""
        super().__init__(**kwargs)
        self._recorded: list[str] = []

    def clear_recorded(self) -> None:
        """Clear the internal recorded-lines buffer."""
        self._recorded.clear()

    @property
    def recorded_lines(self) -> list[str]:
        """Return recorded output lines (for testing/assertions).

        Returns:
            Copy of all appended lines.
        """
        return list(self._recorded)

    def append_text(self, text: str, style: str | None = None) -> None:
        """Write text to the output log, optionally styled.

        Args:
            text: Content to display.
            style: Optional Rich style string.
        """
        self._recorded.append(text)
        if style:
            self.write(Text(text, style=style))
        else:
            self.write(text)

    def append_tool_use(
        self, name: str, args: str, result: str, style: str | None = None
    ) -> None:
        """Write compact tool use line, optionally styled.

        Format: gear name(args) arrow result

        Args:
            name: Tool name.
            args: Tool arguments.
            result: Tool result summary.
            style: Optional Rich style string.
        """
        line = f"\u2699 {name}({args}) \u2192 {result}"
        self._recorded.append(line)
        if style:
            self.write(Text(line, style=style))
        else:
            self.write(line)
