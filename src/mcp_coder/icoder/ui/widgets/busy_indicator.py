"""BusyIndicator widget — spinner animation with elapsed time."""

from __future__ import annotations

from time import monotonic

from textual.widgets import Static

SPINNER_FRAMES: tuple[str, ...] = (
    "⠋",
    "⠙",
    "⠹",
    "⠸",
    "⠼",
    "⠴",
    "⠦",
    "⠧",
    "⠇",
    "⠏",
)


class BusyIndicator(Static):
    """Shows a spinner animation while the LLM is processing."""

    def __init__(self) -> None:
        super().__init__("✓ Ready")
        self._busy: bool = False
        self._message: str = ""
        self._start_time: float = 0.0
        self._frame: int = 0
        self._label: str = "✓ Ready"

    def on_mount(self) -> None:
        """Start the tick interval and show ready state."""
        self.set_interval(0.15, self._on_tick)
        self._set_label("✓ Ready")

    @property
    def label_text(self) -> str:
        """Return the current label text."""
        return self._label

    def show_busy(self, message: str) -> None:
        """Set busy state with the given status message."""
        if not self._busy:
            self._start_time = monotonic()
        self._busy = True
        self._message = message
        self._update_label()

    def show_ready(self) -> None:
        """Reset to idle ready state."""
        self._busy = False
        self._set_label("✓ Ready")

    def _on_tick(self) -> None:
        """Advance spinner frame if busy."""
        if not self._busy:
            return
        self._frame = (self._frame + 1) % len(SPINNER_FRAMES)
        self._update_label()

    def _set_label(self, text: str) -> None:
        """Set label text and update the widget."""
        self._label = text
        self.update(text)

    def _update_label(self) -> None:
        """Update the rendered label with spinner, message, and elapsed time."""
        elapsed = monotonic() - self._start_time
        self._set_label(
            f"{SPINNER_FRAMES[self._frame]} {self._message} [{elapsed:.1f}s]"
        )
