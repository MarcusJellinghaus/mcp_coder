"""Minimal TUI for manual terminal verification (issue #780)."""

from textual.app import App, ComposeResult
from textual.widgets import RichLog


class TestScrollApp(App):
    """App with a single RichLog filled with scrollable lines."""

    def compose(self) -> ComposeResult:
        """Build the widget tree.

        Yields:
            The RichLog widget.
        """
        yield RichLog()

    def on_mount(self) -> None:
        """Fill the log with test lines."""
        log = self.query_one(RichLog)
        for i in range(100):
            log.write(f"Line {i}: scroll test — mouse and rendering check")


if __name__ == "__main__":
    TestScrollApp().run()
