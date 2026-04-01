"""InputArea widget — text input with Enter=submit, Shift-Enter=newline."""

from __future__ import annotations

from typing import Any

from textual import events
from textual.message import Message
from textual.widgets import TextArea

from mcp_coder.icoder.core.command_history import CommandHistory


class InputArea(TextArea):
    """Text input with Enter=submit, Shift-Enter=newline.

    Posts InputSubmitted message when Enter is pressed.
    Up/Down arrow keys navigate command history at boundary lines.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.command_history = CommandHistory()

    class InputSubmitted(Message):
        """Posted when user presses Enter to submit input."""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    async def _on_key(self, event: events.Key) -> None:
        """Intercept Enter vs Shift-Enter.

        Enter submits input and clears the area.
        Shift-Enter inserts a newline (default TextArea behaviour).
        """
        if event.key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text.strip()
            if text:
                self.post_message(self.InputSubmitted(text))
                self.clear()
            return
        if event.key == "shift+enter":
            event.stop()
            event.prevent_default()
            start, end = self.selection
            self._replace_via_keyboard("\n", start, end)
            return
        if event.key == "up":
            cursor_row, _ = self.cursor_location
            if cursor_row == 0:
                entry = self.command_history.up(self.text)
                if entry is not None:
                    event.stop()
                    event.prevent_default()
                    self.load_text(entry)
                    self.move_cursor(self.document.end)
                    return
        if event.key == "down":
            cursor_row, _ = self.cursor_location
            last_row = self.document.line_count - 1
            if cursor_row == last_row:
                entry = self.command_history.down()
                if entry is not None:
                    event.stop()
                    event.prevent_default()
                    self.load_text(entry)
                    self.move_cursor(self.document.end)
                    return
        await super()._on_key(event)
