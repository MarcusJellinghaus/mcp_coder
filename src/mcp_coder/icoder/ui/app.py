"""ICoderApp — Textual App wiring UI events to AppCore."""

from __future__ import annotations

import importlib.metadata
import threading
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
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
from mcp_coder.llm.formatting.stream_renderer import (
    StreamEventRenderer,
    format_tool_start,
)
from mcp_coder.llm.types import StreamEvent
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

STYLE_USER_INPUT = "white on grey23"
STYLE_TOOL_OUTPUT = "white on #0a0a2e"
STYLE_CANCELLED = "dim #e8a838"


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
    BINDINGS = [
        Binding("escape", "cancel_stream", "Cancel", show=False),
        Binding("ctrl+c", "noop", "Copy", show=False),
    ]

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
        self._renderer = StreamEventRenderer(format_tools=format_tools)
        self._text_buffer: str = ""
        self._cancel_event = threading.Event()

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
            command_history=self._core.command_history,
            registry=self._core.registry,
            event_log=self._core.event_log,
        )
        version = self._get_version()
        with Horizontal(id="status-bar"):
            yield Static("↓0 ↑0 | total: ↓0 ↑0", id="status-tokens")
            yield Static(f"v{version}", id="status-version")
            yield Static(r"\ + Enter = newline", id="status-hint")

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
        self._core.command_history.add(text)
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
            self.query_one(BusyIndicator).show_busy("Querying LLM...")
            llm_input = response.llm_text or text
            self.run_worker(lambda: self._stream_llm(llm_input), thread=True)

    def action_cancel_stream(self) -> None:
        """Set cancel event if currently streaming. No-op otherwise."""
        self._cancel_event.set()

    def action_noop(self) -> None:
        """Suppress Ctrl+C quit dialog."""

    def _stream_llm(self, text: str) -> None:
        """Worker target: stream LLM response in background thread.

        Uses call_from_thread() to post updates to the UI event loop.

        Args:
            text: User input to send to LLM.
        """
        self._cancel_event.clear()
        _error_handled = False
        try:
            for event in self._core.stream_llm(text):
                if self._cancel_event.is_set():
                    break
                self.call_from_thread(self._handle_stream_event, event)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _error_handled = True
            self.call_from_thread(self._flush_buffer)
            self.call_from_thread(self._show_error, str(exc))
            self.call_from_thread(self._reset_busy_indicator)
            self.call_from_thread(self._append_blank_line)
        finally:
            if self._cancel_event.is_set() and not _error_handled:
                self.call_from_thread(self._flush_buffer)
                self.call_from_thread(self._append_cancelled_marker)
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
            self._update_token_display()
            self._append_blank_line()
        elif isinstance(action, ToolStart):
            self.query_one(BusyIndicator).show_busy(action.display_name)
            lines = format_tool_start(action, full=False)
            output.append_text("\n".join(lines), style=STYLE_TOOL_OUTPUT)
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
            output.append_text(body, style=STYLE_TOOL_OUTPUT)
        elif isinstance(action, ErrorMessage):
            output.append_text(f"Error: {action.message}")

    def _reset_busy_indicator(self) -> None:
        """Reset busy indicator to ready state."""
        self.query_one(BusyIndicator).show_ready()

    def _append_cancelled_marker(self) -> None:
        """Append dim orange '— Cancelled —' marker to output."""
        self.query_one(OutputLog).append_text("— Cancelled —", style=STYLE_CANCELLED)

    def _show_error(self, message: str) -> None:
        """Display error message in output log.

        Args:
            message: Error text to display.
        """
        self.query_one(OutputLog).append_text(f"Error: {message}")

    def _get_version(self) -> str:
        """Return mcp-coder version from runtime info or package metadata."""
        if self._core.runtime_info:
            return self._core.runtime_info.mcp_coder_version
        try:
            return importlib.metadata.version("mcp-coder")
        except importlib.metadata.PackageNotFoundError:
            return "unknown"

    def _update_token_display(self) -> None:
        """Update status bar token zone from app_core.token_usage."""
        usage = self._core.token_usage
        token_widget = self.query_one("#status-tokens", Static)
        if usage.has_data:
            token_widget.update(usage.display_text())
            token_widget.remove_class("hidden")
        else:
            token_widget.add_class("hidden")
