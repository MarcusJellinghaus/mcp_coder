"""AppCore — Central input router for iCoder. No Textual dependency."""

from __future__ import annotations

from typing import Iterator

from mcp_coder.icoder.core.command_history import CommandHistory
from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import Response, TokenUsage
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
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            llm_service: LLM service for non-command input
            event_log: Structured event log
            registry: Command registry (default: create_default_registry())
            runtime_info: Optional runtime environment info from env_setup
        """
        self._llm_service = llm_service
        self._event_log = event_log
        self._registry = registry if registry is not None else create_default_registry()
        self._runtime_info = runtime_info
        self._token_usage = TokenUsage()
        self._command_history = CommandHistory()

    def handle_input(self, text: str) -> Response:
        """Route user input to commands or flag for LLM streaming.

        - Slash commands: dispatch via registry, emit events, return Response
        - Empty input: ignore (return empty Response)
        - Other text: return Response(send_to_llm=True) so UI can start streaming

        Always emits "input_received" event for non-empty input.

        Returns:
            Response with command output or send_to_llm flag.
        """
        text = text.strip()
        if not text:
            return Response()

        self._event_log.emit("input_received", text=text)

        response = self._registry.dispatch(text)
        if response is not None:
            self._event_log.emit("command_matched", command=text.split()[0].lower())
            if response.text:
                self._event_log.emit("output_emitted", text=response.text)
            if response.reset_session:
                self._llm_service.reset_session()
                self._event_log.emit("session_reset")
            return response

        # Not a command → send to LLM
        return Response(send_to_llm=True)

    def stream_llm(self, text: str) -> Iterator[StreamEvent]:
        """Stream LLM response and auto-store for session continuation.

        Called by UI layer after handle_input() returns send_to_llm=True.
        Emits events for each stream phase. After streaming completes,
        stores the response so ``--continue-session`` can find it.

        Yields:
            StreamEvent dicts for UI to render.
        """
        assembler = ResponseAssembler(self._llm_service.provider)
        self._event_log.emit("llm_request_start", text=text)

        for event in self._llm_service.stream(text):
            assembler.add(event)
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
        store_session(response_data, text)

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
    def session_id(self) -> str | None:
        """Current session ID from LLM service."""
        return self._llm_service.session_id
