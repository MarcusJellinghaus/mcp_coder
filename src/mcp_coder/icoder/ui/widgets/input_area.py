"""InputArea widget — text input with Enter=submit, Shift-Enter=newline."""

from __future__ import annotations

from textual import events
from textual.message import Message
from textual.widgets import TextArea


class InputArea(TextArea):
    """Text input with Enter=submit, Shift-Enter=newline.

    Posts InputSubmitted message when Enter is pressed.
    """

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
        await super()._on_key(event)
