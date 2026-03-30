"""OutputLog widget — scrollable output area for conversation display."""

from __future__ import annotations

from typing import Any

from textual.widgets import RichLog


class OutputLog(RichLog):
    """Scrollable output area for conversation display."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with internal line buffer for testability."""
        super().__init__(**kwargs)
        self._recorded: list[str] = []

    @property
    def recorded_lines(self) -> list[str]:
        """Return recorded output lines (for testing/assertions).

        Returns:
            Copy of all appended lines.
        """
        return list(self._recorded)

    def append_text(self, text: str) -> None:
        """Write text to the output log.

        Also appends to internal line buffer.
        """
        self._recorded.append(text)
        self.write(text)

    def append_tool_use(self, name: str, args: str, result: str) -> None:
        """Write compact tool use line.

        Format: gear name(args) arrow result
        """
        line = f"\u2699 {name}({args}) \u2192 {result}"
        self._recorded.append(line)
        self.write(line)
