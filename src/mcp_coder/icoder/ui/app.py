"""ICoderApp — Textual App wiring UI events to AppCore."""

from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.ui.styles import CSS
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent

STYLE_USER_INPUT = "white on grey23"
STYLE_TOOL_OUTPUT = "white on #0a0a2e"


class ICoderApp(App[None]):
    """Interactive coding TUI. Thin shell over AppCore."""

    CSS = CSS

    def __init__(self, app_core: AppCore, **kwargs: Any) -> None:
        """Initialize with injected AppCore.

        Args:
            app_core: Central input router.
            **kwargs: Passed to App.__init__.
        """
        super().__init__(**kwargs)
        self._core = app_core

    def compose(self) -> ComposeResult:
        """Vertical layout: OutputLog on top, InputArea at bottom.

        Yields:
            OutputLog and InputArea widgets.
        """
        yield OutputLog()
        yield InputArea()

    def on_mount(self) -> None:
        """Focus input area on startup."""
        self.query_one(InputArea).focus()

    def on_input_area_input_submitted(self, message: InputArea.InputSubmitted) -> None:
        """Handle submitted input: route through AppCore."""
        text = message.text
        output = self.query_one(OutputLog)
        output.append_text(f"> {text}", style=STYLE_USER_INPUT)

        response = self._core.handle_input(text)
        if response.quit:
            self.exit()
        elif response.clear_output:
            output.clear()
            output.clear_recorded()
        elif response.text:
            output.append_text(response.text)
        elif response.send_to_llm:
            output.write("")
            self.run_worker(lambda: self._stream_llm(text), thread=True)

    def _stream_llm(self, text: str) -> None:
        """Worker target: stream LLM response in background thread.

        Uses call_from_thread() to post updates to the UI event loop.

        Args:
            text: User input to send to LLM.
        """
        try:
            for event in self._core.stream_llm(text):
                self.call_from_thread(self._handle_stream_event, event)
            self.call_from_thread(self._append_blank_line)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.call_from_thread(self._show_error, str(exc))

    def _append_blank_line(self) -> None:
        """Write an empty line to the output log for visual spacing."""
        self.query_one(OutputLog).write("")

    def _handle_stream_event(self, event: StreamEvent) -> None:
        """Render a single stream event in the output log.

        Args:
            event: StreamEvent dict with a "type" key.
        """
        output = self.query_one(OutputLog)
        event_type = event.get("type")
        if event_type == "text_delta":
            text = event.get("text", "")
            if isinstance(text, str) and text:
                output.append_text(text)
        elif event_type == "tool_use_start":
            name = str(event.get("name", ""))
            args = str(event.get("args", {}))
            output.append_tool_use(name, args, "...", style=STYLE_TOOL_OUTPUT)
        elif event_type == "tool_result":
            name = str(event.get("name", ""))
            output.append_tool_use(name, "", "done", style=STYLE_TOOL_OUTPUT)
        elif event_type == "error":
            msg = event.get("message", "Unknown error")
            output.append_text(f"Error: {msg}")

    def _show_error(self, message: str) -> None:
        """Display error message in output log.

        Args:
            message: Error text to display.
        """
        self.query_one(OutputLog).append_text(f"Error: {message}")
