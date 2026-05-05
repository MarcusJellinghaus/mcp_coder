"""ICoderApp — Textual App wiring UI events to AppCore."""

from __future__ import annotations

import importlib.metadata
import logging
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.services.branch_info_service import BranchInfoService
from mcp_coder.icoder.ui.styles import CSS
from mcp_coder.icoder.ui.widgets.branch_info_bar import BranchInfoBar, BranchInfoView
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
from mcp_coder.services.branch_info import BranchInfo
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

logger = logging.getLogger(__name__)

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
        self._project_dir: Path = (
            Path(app_core.runtime_info.project_dir)
            if app_core.runtime_info
            else Path.cwd()
        )
        self._branch_service = BranchInfoService(self._project_dir)
        self._branch_loading: set[str] = set()
        self._branch_failed: set[str] = set()
        self._last_branch_info: Optional[BranchInfo] = None
        self._last_pr_number: Optional[int] = None
        self._last_view: Optional[BranchInfoView] = None

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
            yield Static(f"mcp-coder v{version}", id="status-version")
            yield Static(r"\ + Enter = newline", id="status-hint")
        yield BranchInfoBar(self._project_dir)

    def on_mount(self) -> None:
        """Display startup info and focus input area."""
        if self._core.runtime_info:
            info = self._core.runtime_info
            output = self.query_one(OutputLog)
            lines = [
                f"mcp-coder {info.mcp_coder_version}",
                f"mcp-coder-utils {info.mcp_coder_utils_version}",
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
        self._apply_prompt_border()
        self.query_one(InputArea).focus()
        self.query_one(BranchInfoBar).update_state(None)
        self.run_worker(self._tick_branch_full, thread=True)
        self.set_interval(10.0, self._tick_branch_quick)
        self.set_interval(30.0, self._tick_branch_full)

    def on_input_area_input_submitted(self, message: InputArea.InputSubmitted) -> None:
        """Handle submitted input: route through AppCore."""
        text = message.text
        self._core.command_history.add(text)
        output = self.query_one(OutputLog)
        output.append_text(f"> {text}", style=STYLE_USER_INPUT)

        response = self._core.handle_input(text)
        self._apply_prompt_border()
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
            elif not _error_handled:
                self.call_from_thread(self._reset_busy_indicator)

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
            self.query_one(BusyIndicator).show_busy(f"Thinking about {action.name}...")
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

    def _apply_prompt_border(self) -> None:
        """Apply current prompt color as InputArea border."""
        from textual.color import Color

        color = Color.parse(self._core.prompt_color)
        self.query_one(InputArea).styles.border = ("round", color)

    def _update_token_display(self) -> None:
        """Update status bar token zone from app_core.token_usage."""
        usage = self._core.token_usage
        token_widget = self.query_one("#status-tokens", Static)
        if usage.has_data:
            token_widget.update(usage.display_text())
            token_widget.remove_class("hidden")
        else:
            token_widget.add_class("hidden")

    # ------------------------------------------------------------------
    # Branch info wiring
    # ------------------------------------------------------------------

    def _tick_branch_quick(self) -> None:
        """10-second tick: fetch branch state; auto-kick PR fetch on change."""
        self.run_worker(self._branch_quick_work, thread=True)

    def _tick_branch_full(self) -> None:
        """30-second tick: full refresh including issue cache reload."""
        self.run_worker(self._branch_full_work, thread=True)

    def _timed_fetch(self, label: str, fn: Callable[[], BranchInfo]) -> BranchInfo:
        """Wrap a data-layer fetch with debug-level perf timing.

        Args:
            label: Identifier used in the debug log line.
            fn: Zero-arg callable returning a ``BranchInfo``.

        Returns:
            The ``BranchInfo`` produced by ``fn``.
        """
        start = time.perf_counter()
        try:
            return fn()
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.debug("%s: %dms", label, elapsed_ms)

    def _branch_quick_work(self) -> None:
        """Worker body for the 10s branch tick."""
        if not self._branch_service.begin_quick_tick():
            return
        info: Optional[BranchInfo] = None
        try:
            info = self._timed_fetch(
                "branch_quick", self._branch_service.fetch_branch_only
            )
            self._branch_failed.discard("issue")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("branch_quick fetch failed: %s", exc)
            self._branch_failed.add("issue")
        finally:
            self._branch_service.end_quick_tick()
        self.call_from_thread(self._apply_branch_state, info, merge_with_prior=True)

    def _branch_full_work(self) -> None:
        """Worker body for the 30s branch tick (with loading marker)."""
        if not self._branch_service.begin_full_tick():
            return
        self._branch_loading.add("issue")
        self.call_from_thread(self._render_branch_state)
        info: Optional[BranchInfo] = None
        try:
            info = self._timed_fetch("branch_full", self._branch_service.fetch_info)
            self._branch_failed.discard("issue")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("branch_full fetch failed: %s", exc)
            self._branch_failed.add("issue")
        finally:
            self._branch_loading.discard("issue")
            self._branch_service.end_full_tick()
        self.call_from_thread(self._apply_branch_state, info)

    def on_branch_info_bar_refresh_issue(self, _: BranchInfoBar.RefreshIssue) -> None:
        """Refresh-issue button handler."""
        if not self._branch_service.begin_issue_fetch():
            return
        self._branch_loading.add("issue")
        self._render_branch_state()
        self.run_worker(self._refresh_issue_work, thread=True)

    def _refresh_issue_work(self) -> None:
        """Worker body for the refresh-issue button."""
        try:
            info: Optional[BranchInfo] = self._branch_service.fetch_info()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("refresh_issue fetch_info failed: %s", exc)
            self._branch_failed.add("issue")
            info = None
        else:
            self._branch_failed.discard("issue")
        finally:
            self._branch_loading.discard("issue")
            self._branch_service.end_issue_fetch()
        self.call_from_thread(self._apply_branch_state, info)

    def on_branch_info_bar_refresh_pr(self, _: BranchInfoBar.RefreshPR) -> None:
        """Refresh-PR button handler. Fires regardless of toggle state."""
        info = self._last_branch_info
        if info is None or info.issue_number is None:
            return
        if not self._branch_service.begin_pr_fetch():
            return
        self._branch_loading.add("pr")
        self._render_branch_state()
        self._launch_pr_worker(info.issue_number)

    def on_branch_info_bar_toggle_pr(self, _: BranchInfoBar.TogglePR) -> None:
        """Toggle-PR handler: flip state, optionally kick PR fetch."""
        new_value = not self._branch_service.pr_enabled
        self._branch_service.set_pr_enabled(new_value)
        if not new_value:
            self._last_pr_number = None
            self._branch_loading.discard("pr")
            self._branch_failed.discard("pr")
        self._render_branch_state()
        if new_value:
            info = self._last_branch_info
            if info is not None and info.issue_number is not None:
                # Route through begin_pr_fetch so the in-flight guard is
                # uniform across toggle-on and refresh-PR launch paths.
                if self._branch_service.begin_pr_fetch():
                    self._branch_loading.add("pr")
                    self._render_branch_state()
                    self._launch_pr_worker(info.issue_number)

    def _launch_pr_worker(self, issue_number: int) -> None:
        """Capture a PR-fetch generation and spawn the worker."""
        gen = self._branch_service.start_pr_fetch()

        def work() -> None:
            pr_number: Optional[int] = None
            raised = False
            try:
                pr_number = self._branch_service.fetch_pr(issue_number)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.debug("fetch_pr failed: %s", exc)
                raised = True
            # Gate ALL shared-state mutations behind the generation check so a
            # stale worker (invalidated by a newer toggle/refresh) never
            # touches UI flags that belong to a fresher generation.
            if gen != self._branch_service.current_pr_fetch_generation:
                return
            self._branch_service.end_pr_fetch()
            if raised:
                self._branch_failed.add("pr")
            else:
                self._branch_failed.discard("pr")
            self._branch_loading.discard("pr")
            self.call_from_thread(self._apply_pr_result, pr_number)

        self.run_worker(work, thread=True)

    def _apply_branch_state(
        self,
        info: Optional[BranchInfo],
        *,
        merge_with_prior: bool = False,
    ) -> None:
        """Store new branch info, re-render, and auto-kick a PR fetch on change.

        Runs on the UI thread (via ``call_from_thread``). The branch-changed
        check and any auto-PR-kick must live here, not in the worker thread,
        so concurrent quick-ticks cannot race ``_last_branch`` or the PR-fetch
        generation token.

        When ``merge_with_prior`` is True (quick-tick path), the issue title,
        status label, and cache-age timestamp are copied from the prior
        ``_last_branch_info`` so they are not lost between full ticks.
        """
        if info is not None and merge_with_prior and self._last_branch_info is not None:
            info = replace(
                info,
                issue_title=self._last_branch_info.issue_title,
                issue_status_label=self._last_branch_info.issue_status_label,
                cache_last_checked=self._last_branch_info.cache_last_checked,
            )
        if info is not None:
            self._last_branch_info = info
        self._render_branch_state()
        if (
            info is not None
            and self._branch_service.branch_changed(info.branch_name)
            and self._branch_service.pr_enabled
            and info.issue_number is not None
        ):
            self._launch_pr_worker(info.issue_number)

    def _apply_pr_result(self, pr_number: Optional[int]) -> None:
        """Unconditionally store a PR worker's result and re-render.

        Unlike ``_apply_branch_state``, this writes ``pr_number`` even when it
        is ``None`` so a refresh that discovers the PR no longer exists clears
        the previously cached value (otherwise the bar keeps showing the stale
        ``PR #N``).
        """
        self._last_pr_number = pr_number
        self._render_branch_state()

    def _render_branch_state(self) -> None:
        """Render current state into the BranchInfoBar."""
        try:
            bar = self.query_one(BranchInfoBar)
        except NoMatches:
            return
        if self._last_branch_info is None:
            new_view: Optional[BranchInfoView] = None
        else:
            new_view = BranchInfoView(
                info=self._last_branch_info,
                pr_number=self._last_pr_number,
                pr_enabled=self._branch_service.pr_enabled,
                loading=frozenset(self._branch_loading),
                failed=frozenset(self._branch_failed),
            )
        if new_view == self._last_view:
            return
        self._last_view = new_view
        bar.update_state(new_view)
