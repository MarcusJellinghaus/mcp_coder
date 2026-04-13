"""Minimal TUI for manual terminal verification (issue #780)."""
from textual.app import App, ComposeResult
from textual.widgets import RichLog


class TestScrollApp(App):
    def compose(self) -> ComposeResult:
        yield RichLog()

    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        for i in range(100):
            log.write(f"Line {i}: scroll test — mouse and rendering check")


if __name__ == "__main__":
    TestScrollApp().run()
