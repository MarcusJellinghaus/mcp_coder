"""OutputLog widget — scrollable output area for conversation display."""

from __future__ import annotations

from typing import Any

from rich.console import ConsoleRenderable, RichCast
from rich.text import Text
from textual.widgets import RichLog


class OutputLog(RichLog):
    """Scrollable output area for conversation display."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with internal line buffer for testability."""
        super().__init__(wrap=True, **kwargs)
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

    def write(  # type: ignore[override]  # pylint: disable=arguments-differ
        self,
        content: RichCast | ConsoleRenderable | str | object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Write content and record a text representation for testability.

        Overrides RichLog.write() to also track non-string renderables
        (e.g. Markdown objects) in _recorded.

        Args:
            content: Rich renderable, string, or other object to display.
            *args: Positional args passed through to RichLog.write().
            **kwargs: Keyword args passed through to RichLog.write().
        """
        if isinstance(content, str):
            # Plain strings are NOT recorded by write(); use append_text() for recorded text.
            pass
        elif isinstance(content, Text):
            # Text objects are recorded via append_text, skip here
            pass
        else:
            # Rich renderables (e.g. Markdown): record the markup text
            markup = getattr(content, "markup", None)
            self._recorded.append(markup if markup is not None else str(content))
        super().write(content, *args, **kwargs)

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
