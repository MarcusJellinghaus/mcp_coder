"""AppCore — Central input router for iCoder. No Textual dependency."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterator, Literal

from mcp_coder.icoder.core.colors import DEFAULT_PROMPT_COLOR, validate_color
from mcp_coder.icoder.core.command_history import CommandHistory
from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.event_log import (
    EventLog,
    emit_session_start,
    read_session_id_from_log,
)
from mcp_coder.icoder.core.types import (
    Action,
    OutputText,
    ResetSession,
    Response,
    SendToLLM,
    TokenUsage,
)
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import LLMService
from mcp_coder.llm.storage import store_session
from mcp_coder.llm.types import ResponseAssembler, StreamEvent


class AppCore:
    """Central input router. No Textual dependency."""

    def __init__(
        self,
        llm_service: LLMService,
        event_log: EventLog,
        registry: CommandRegistry | None = None,
        runtime_info: RuntimeInfo | None = None,
        tool_display: Literal["oneline", "compressed"] = "compressed",
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            llm_service: LLM service for non-command input
            event_log: Structured event log
            registry: Command registry (default: create_default_registry())
            runtime_info: Optional runtime environment info from env_setup
            tool_display: Initial global tool-display tier (default
                ``"compressed"``). Set by the ``--tool-display`` CLI flag.
        """
        self._llm_service = llm_service
        self._event_log = event_log
        self._registry = registry if registry is not None else create_default_registry()
        self._runtime_info = runtime_info
        self._token_usage = TokenUsage()
        self._command_history = CommandHistory()
        self._prompt_color: str = DEFAULT_PROMPT_COLOR
        self._tool_display: Literal["oneline", "compressed"] = tool_display

    def handle_input(self, text: str) -> Response:
        """Route user input to commands or typed actions for the UI.

        - Slash commands: dispatch via registry, perform state-mutating
          side effects (output_emitted events, session reset), and return
          the command's typed-action Response.
        - Empty input: ignore (return empty ``Response()``).
        - Other text: return ``Response(actions=(SendToLLM(text=text),))``
          so the UI can start streaming.

        All state-mutation side effects (event-log rotation, session reset,
        output_emitted emission) happen here, BEFORE returning; the UI then
        iterates ``response.actions`` in tuple order. ``SendToLLM`` actions
        are resolved here so an empty ``text`` (skill passthrough) becomes
        the original user input.

        Always emits "input_received" event for non-empty input.

        Returns:
            Response whose ``actions`` the UI dispatches in order.
        """
        text = text.strip()
        if not text:
            return Response()

        self._event_log.emit("input_received", text=text)

        response = self._registry.dispatch(text)
        if response is not None:
            self._event_log.emit("command_matched", command=text.split()[0].lower())
            resolved: list[Action] = []
            for action in response.actions:
                if isinstance(action, OutputText):
                    self._event_log.emit("output_emitted", text=action.text)
                    resolved.append(action)
                elif isinstance(action, ResetSession):
                    self._reset_session()
                    resolved.append(action)
                elif isinstance(action, SendToLLM):
                    resolved.append(replace(action, text=action.text or text))
                else:
                    resolved.append(action)
            return Response(actions=tuple(resolved))

        # Not a command → send to LLM
        return Response(actions=(SendToLLM(text=text),))

    def _reset_session(self) -> None:
        """Reset the LLM session and rotate the event log.

        The rotated log starts empty — emit a fresh session_start so the
        post-/clear file remains self-contained and visible to the startup
        picker (which filters on provider).
        """
        self._llm_service.reset_session()
        self._event_log.rotate()
        emit_session_start(
            self._event_log,
            provider=self._llm_service.provider,
            runtime_info=self._runtime_info,
            session_id=self._llm_service.session_id,
        )

    def stream_llm(
        self, text: str, allowed_tools: tuple[str, ...] | None = None
    ) -> Iterator[StreamEvent]:
        """Stream LLM response and auto-store for session continuation.

        Called by the UI layer when dispatching a ``SendToLLM`` action.
        Emits events for each stream phase. After streaming completes,
        stores the response so ``--continue-session`` can find it.

        Args:
            text: User input to send to the LLM.
            allowed_tools: Declared MCP tool tokens for this turn (from a
                skill's ``SendToLLM.allowed_tools``), forwarded to the
                service for host-side enforcement, or ``None``.

        Yields:
            StreamEvent dicts for UI to render.
        """
        assembler = ResponseAssembler(self._llm_service.provider)
        self._event_log.emit("llm_request_start", text=text)

        for event in self._llm_service.stream(text, allowed_tools):
            assembler.add(event)
            if event.get("type") != "raw_line":
                self._event_log.emit("stream_event", **event)
            if event.get("type") == "done":
                usage = event.get("usage", {})
                if isinstance(usage, dict):
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    if (
                        isinstance(input_tokens, int)
                        and isinstance(output_tokens, int)
                        and isinstance(cache_read, int)
                    ):
                        self._token_usage.update(
                            input_tokens, output_tokens, cache_read
                        )
            yield event

        self._event_log.emit("llm_request_end")

        # Auto-store response for --continue-session
        response_data = assembler.result()
        store_session(
            response_data, text, log_file_path=str(self._event_log.current_path)
        )

    @property
    def command_history(self) -> CommandHistory:
        """Command history for Up/Down recall. Survives /clear."""
        return self._command_history

    @property
    def registry(self) -> CommandRegistry:
        """Public read-only access to the command registry."""
        return self._registry

    @property
    def event_log(self) -> EventLog:
        """Public read-only access to the event log."""
        return self._event_log

    @property
    def runtime_info(self) -> RuntimeInfo | None:
        """Runtime environment info, if provided."""
        return self._runtime_info

    @property
    def token_usage(self) -> TokenUsage:
        """Cumulative token usage for this session."""
        return self._token_usage

    @property
    def prompt_color(self) -> str:
        """Current prompt border color as hex string. Always concrete, never None."""
        return self._prompt_color

    def set_prompt_color(self, value: str) -> str | None:
        """Validate and set prompt border color. Delegates to validate_color().

        Returns:
            Error message string on failure, None on success.
        """
        hex_color, error = validate_color(value)
        if error:
            return error
        self._prompt_color = hex_color  # type: ignore[assignment]
        return None

    @property
    def tool_display(self) -> str:
        """Current global tool-display tier ("oneline" or "compressed")."""
        return self._tool_display

    def set_tool_display(self, value: Literal["oneline", "compressed"]) -> None:
        """Set the global tool-display tier and emit a change event.

        Args:
            value: The new global tier ("oneline" or "compressed").
        """
        self._tool_display = value
        self._event_log.emit("display_mode_changed", to=value)

    @property
    def session_id(self) -> str | None:
        """Current session ID from LLM service."""
        return self._llm_service.session_id

    @property
    def provider(self) -> str:
        """Current LLM provider name from the LLM service."""
        return self._llm_service.provider

    def prepare_for_resume(self, log_path: Path) -> str | None:
        """Resolve a session_id from a prior log and rotate the event log.

        Delegates id resolution to ``read_session_id_from_log``; the
        resolved id (or ``None``) is set on the LLM service. The event
        log is rotated so the new conversation gets its own JSONL file,
        and a fresh ``session_start`` (with the current provider /
        runtime_info / session_id) is emitted so the resumed-from log
        is self-contained and visible to future pickers.

        Returns:
            The resolved session_id string, or ``None`` if no candidate
            was found in the log.
        """
        session_id = read_session_id_from_log(log_path)
        self._llm_service.set_session_id(session_id)
        self._event_log.rotate()
        emit_session_start(
            self._event_log,
            provider=self._llm_service.provider,
            runtime_info=self._runtime_info,
            session_id=self._llm_service.session_id,
        )
        return session_id
