"""ICoderApp — Textual App wiring UI events to AppCore."""

from __future__ import annotations

from typing import Any

from rich.markdown import Markdown
from textual.app import App, ComposeResult
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.ui.styles import CSS
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.command_autocomplete import CommandAutocomplete
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.formatting.render_actions import (
    ErrorMessage,
    StreamDone,
    TextChunk,
    ToolResult,
    ToolStart,
)
from mcp_coder.llm.formatting.stream_renderer import StreamEventRenderer
from mcp_coder.llm.types import StreamEvent
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

STYLE_USER_INPUT = "white on grey23"
STYLE_TOOL_OUTPUT = "white on #0a0a2e"


def _connection_status_suffix(
    server_name: str,
    statuses: list[ClaudeMCPStatus] | None,
) -> str:
    """Return '✓ Connected' or '✗ <text>' for a server, or '' if not found."""
    if statuses is None:
        return ""
    for status in statuses:
        if status.name == server_name:
            if status.ok:
                return "✓ Connected"
            return f"✗ {status.status_text}"
    return ""


class ICoderApp(App[None]):
    """Interactive coding TUI. Thin shell over AppCore."""

    CSS = CSS

    def __init__(
        self, app_core: AppCore, *, format_tools: bool = True, **kwargs: Any
    ) -> None:
        """Initialize with injected AppCore.

        Args:
            app_core: Central input router.
            format_tools: Enable tool output formatting (default True).
            **kwargs: Passed to App.__init__.
        """
        super().__init__(**kwargs)
        self._core = app_core
        self._format_tools = format_tools
        self._renderer = StreamEventRenderer(format_tools=format_tools)
        self._text_buffer: str = ""

    def compose(self) -> ComposeResult:
        """Vertical layout: OutputLog on top, InputArea at bottom.

        Yields:
            OutputLog and InputArea widgets.
        """
        yield OutputLog()
        yield Static(id="streaming-tail")
        yield CommandAutocomplete()
        yield BusyIndicator()
        yield InputArea(
            registry=self._core.registry,
            event_log=self._core.event_log,
        )
        yield Static(r"\ + Enter = newline", id="input-hint")

    def on_text_area_changed(self) -> None:
        """Toggle input hint visibility based on whether input is empty."""
        hint = self.query_one("#input-hint", Static)
        input_area = self.query_one(InputArea)
        if input_area.text:
            hint.add_class("hidden")
        else:
            hint.remove_class("hidden")

    def on_mount(self) -> None:
        """Display startup info and focus input area."""
        if self._core.runtime_info:
            info = self._core.runtime_info
            output = self.query_one(OutputLog)
            lines = [
                f"mcp-coder {info.mcp_coder_version}",
                *(
                    (
                        f"{s.name} {s.version}  {_connection_status_suffix(s.name, info.mcp_connection_status)}".rstrip()
                        if info.mcp_connection_status is not None
                        else f"{s.name} {s.version}"
                    )
                    for s in info.mcp_servers
                ),
                f"Tool env:    {info.tool_env_path}",
                f"Project env: {info.project_venv_path}",
                f"Project dir: {info.project_dir}",
            ]
            output.append_text("\n".join(lines), style="dim")
        self.query_one(InputArea).focus()

    def on_input_area_input_submitted(self, message: InputArea.InputSubmitted) -> None:
        """Handle submitted input: route through AppCore."""
        text = message.text
        self.query_one(InputArea).command_history.add(text)
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
            llm_input = response.llm_text or text
            self.run_worker(lambda: self._stream_llm(llm_input), thread=True)

    def _stream_llm(self, text: str) -> None:
        """Worker target: stream LLM response in background thread.

        Uses call_from_thread() to post updates to the UI event loop.

        Args:
            text: User input to send to LLM.
        """
        try:
            for event in self._core.stream_llm(text):
                self.call_from_thread(self._handle_stream_event, event)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.call_from_thread(self._flush_buffer)
            self.call_from_thread(self._show_error, str(exc))
            self.call_from_thread(self._reset_busy_indicator)
            self.call_from_thread(self._append_blank_line)

    def _append_blank_line(self) -> None:
        """Write an empty line to the output log for visual spacing."""
        self.query_one(OutputLog).write("")

    def _flush_buffer(self) -> None:
        """Flush any buffered text to OutputLog and clear the streaming tail."""
        if self._text_buffer:
            self.query_one(OutputLog).append_text(self._text_buffer)
            self._text_buffer = ""
        self.query_one("#streaming-tail", Static).update("")

    def _handle_stream_event(self, event: StreamEvent) -> None:
        """Render a single stream event in the output log.

        Args:
            event: StreamEvent dict with a "type" key.
        """
        output = self.query_one(OutputLog)
        action = self._renderer.render(event)
        if action is None:
            return

        if isinstance(action, TextChunk):
            self.query_one(BusyIndicator).show_busy("Thinking...")
            self._text_buffer += action.text
            lines = self._text_buffer.split("\n")
            for line in lines[:-1]:
                output.append_text(line)
            self._text_buffer = lines[-1]
            self.query_one("#streaming-tail", Static).update(self._text_buffer)
            return

        # Any non-text action: flush buffer first
        self._flush_buffer()

        if isinstance(action, StreamDone):
            self.query_one(BusyIndicator).show_ready()
            self._append_blank_line()
        elif isinstance(action, ToolStart):
            self.query_one(BusyIndicator).show_busy(action.display_name)
            if action.inline_args is not None:
                line = f"┌ {action.display_name}({action.inline_args})"
            else:
                parts = [f"┌ {action.display_name}"]
                for key, value in action.block_args:
                    parts.append(f"│  {key}: {value}")
                line = "\n".join(parts)
            output.append_text(line, style=STYLE_TOOL_OUTPUT)
        elif isinstance(action, ToolResult):
            parts = [f"│  {ln}" for ln in action.output_lines]
            if action.truncated:
                parts.append(
                    f"└ done ({action.total_lines} lines, "
                    f"truncated to {len(action.output_lines)})"
                )
            else:
                parts.append("└ done")
            body = "\n".join(parts)
            if self._format_tools:
                output.write(Markdown(body))
            else:
                output.append_text(body, style=STYLE_TOOL_OUTPUT)
        elif isinstance(action, ErrorMessage):
            output.append_text(f"Error: {action.message}")

    def _reset_busy_indicator(self) -> None:
        """Reset busy indicator to ready state."""
        self.query_one(BusyIndicator).show_ready()

    def _show_error(self, message: str) -> None:
        """Display error message in output log.

        Args:
            message: Error text to display.
        """
        self.query_one(OutputLog).append_text(f"Error: {message}")
