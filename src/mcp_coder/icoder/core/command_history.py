"""CommandHistory — In-session command history with Up/Down navigation."""

from __future__ import annotations


class CommandHistory:
    """In-session command history with Up/Down navigation.

    Pure Python, no Textual dependency. Stores submitted inputs and
    allows cycling through them with up()/down(), preserving a draft
    of the current input when entering history mode.
    """

    def __init__(self) -> None:
        self._entries: list[str] = []
        self._cursor: int = 0
        self._draft: str = ""

    def add(self, text: str) -> None:
        """Add a command to history.

        Strips whitespace; rejects empty. Suppresses consecutive duplicates.
        Resets navigation cursor.
        """
        text = text.strip()
        if not text:
            return
        if self._entries and self._entries[-1] == text:
            return
        self._entries.append(text)
        self.reset_cursor()

    def up(self, current_text: str) -> str | None:
        """Navigate to older history entry.

        On first call (cursor at end), saves current_text as draft.
        Returns the older entry, or None if empty or already at oldest.
        """
        if not self._entries:
            return None
        if self._cursor == len(self._entries):
            self._draft = current_text
        if self._cursor == 0:
            return None
        self._cursor -= 1
        return self._entries[self._cursor]

    def down(self) -> str | None:
        """Navigate to newer history entry.

        Returns the newer entry, the saved draft when passing the newest,
        or None if already at the draft position.
        """
        if self._cursor >= len(self._entries):
            return None
        self._cursor += 1
        if self._cursor == len(self._entries):
            return self._draft
        return self._entries[self._cursor]

    def reset_cursor(self) -> None:
        """Reset navigation cursor to past-end position and clear draft."""
        self._cursor = len(self._entries)
        self._draft = ""
