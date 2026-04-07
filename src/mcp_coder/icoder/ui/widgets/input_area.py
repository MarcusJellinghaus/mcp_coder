"""InputArea widget — text input with Enter=submit, Shift-Enter=newline."""

from __future__ import annotations

from typing import Any

from textual import events
from textual.css.query import NoMatches
from textual.message import Message
from textual.widgets import TextArea

from mcp_coder.icoder.core.autocomplete_state import (
    AutocompleteState,
    compute_next_state,
)
from mcp_coder.icoder.core.command_history import CommandHistory
from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.ui.widgets.command_autocomplete import CommandAutocomplete


class InputArea(TextArea):
    """Text input with Enter=submit, Shift-Enter=newline.

    Posts InputSubmitted message when Enter is pressed.
    Up/Down arrow keys navigate command history at boundary lines.
    """

    def __init__(
        self,
        *args: Any,
        registry: CommandRegistry | None = None,
        event_log: EventLog | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.command_history = CommandHistory()
        self._registry: CommandRegistry | None = registry
        self._event_log: EventLog | None = event_log
        self._ac_state: AutocompleteState = AutocompleteState(
            visible=False, matches=(), highlighted_index=-1
        )
        self._suppress_ac_recompute: bool = False

    class InputSubmitted(Message):
        """Posted when user presses Enter to submit input."""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def on_text_area_changed(self) -> None:
        """Resize height to match content, capped at 1/3 of screen."""
        if not self.screen:
            return
        line_count = self.document.line_count
        max_lines = max(1, self.screen.size.height // 3)
        self.styles.height = min(line_count + 2, max_lines)

        if self._registry is None:
            return
        if self._suppress_ac_recompute:
            self._suppress_ac_recompute = False
            return

        prev = self._ac_state
        new = compute_next_state(self.text, self._registry)
        self._ac_state = new

        try:
            dropdown = self.screen.query_one(CommandAutocomplete)
        except NoMatches:
            return

        if new.visible:
            dropdown.update_matches(list(new.matches))
            dropdown.show_dropdown()
        else:
            dropdown.hide_dropdown()

        if self._event_log is not None:
            self._emit_ac_event(prev, new)

    def _emit_ac_event(self, prev: AutocompleteState, new: AutocompleteState) -> None:
        """Emit autocomplete transition events based on state diff."""
        assert self._event_log is not None
        if not prev.visible and new.visible:
            self._event_log.emit(
                "autocomplete_shown",
                matches=[c.name for c in new.matches],
            )
        elif prev.visible and new.visible:
            if prev.matches != new.matches:
                self._event_log.emit(
                    "autocomplete_filtered",
                    query=self.text,
                    matches=[c.name for c in new.matches],
                )
        elif prev.visible and not new.visible:
            self._event_log.emit("autocomplete_hidden", reason="prefix_removed")

    async def _on_key(self, event: events.Key) -> None:
        """Intercept Enter vs Shift-Enter.

        Enter submits input and clears the area.
        Shift-Enter inserts a newline (default TextArea behaviour).
        Routes Up/Down/Tab/Escape to dropdown when visible.
        """
        if self._ac_state.visible:
            try:
                dropdown = self.screen.query_one(CommandAutocomplete)
            except NoMatches:
                pass
            else:
                if event.key == "escape":
                    event.stop()
                    event.prevent_default()
                    dropdown.hide_dropdown()
                    self._ac_state = AutocompleteState(
                        visible=False, matches=(), highlighted_index=-1
                    )
                    if self._event_log is not None:
                        self._event_log.emit("autocomplete_hidden", reason="escape")
                        self._event_log.emit("autocomplete_key_routed", key="escape")
                    return

                if event.key == "up":
                    event.stop()
                    event.prevent_default()
                    dropdown.highlight_previous()
                    if self._event_log is not None:
                        self._event_log.emit("autocomplete_key_routed", key="up")
                    return

                if event.key == "down":
                    event.stop()
                    event.prevent_default()
                    dropdown.highlight_next()
                    if self._event_log is not None:
                        self._event_log.emit("autocomplete_key_routed", key="down")
                    return

                if event.key == "tab":
                    event.stop()
                    event.prevent_default()
                    name = dropdown.select_highlighted()
                    if name:
                        self._suppress_ac_recompute = True
                        self.load_text(name + " ")
                        self.move_cursor(self.document.end)
                        if self._event_log is not None:
                            self._event_log.emit("autocomplete_selected", command=name)
                    dropdown.hide_dropdown()
                    self._ac_state = AutocompleteState(
                        visible=False, matches=(), highlighted_index=-1
                    )
                    if self._event_log is not None:
                        self._event_log.emit("autocomplete_hidden", reason="selected")
                        self._event_log.emit("autocomplete_key_routed", key="tab")
                    return

        if event.key == "enter":
            if self._ac_state.visible:
                try:
                    dropdown = self.screen.query_one(CommandAutocomplete)
                except NoMatches:
                    pass
                else:
                    dropdown.hide_dropdown()
                    self._ac_state = AutocompleteState(
                        visible=False, matches=(), highlighted_index=-1
                    )
                    if self._event_log is not None:
                        self._event_log.emit("autocomplete_hidden", reason="submit")
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
                event.stop()
                event.prevent_default()
                if entry is not None:
                    self.load_text(entry)
                    self.move_cursor(self.document.end)
                return
        if event.key == "down":
            cursor_row, _ = self.cursor_location
            last_row = self.document.line_count - 1
            if cursor_row == last_row:
                entry = self.command_history.down()
                event.stop()
                event.prevent_default()
                if entry is not None:
                    self.load_text(entry)
                    self.move_cursor(self.document.end)
                return
        await super()._on_key(event)
