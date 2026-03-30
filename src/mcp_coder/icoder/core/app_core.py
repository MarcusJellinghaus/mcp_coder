"""AppCore — Central input router for iCoder. No Textual dependency."""

from __future__ import annotations

from typing import Iterator

from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import Response
from mcp_coder.icoder.services.llm_service import LLMService
from mcp_coder.llm.types import StreamEvent


class AppCore:
    """Central input router. No Textual dependency."""

    def __init__(
        self,
        llm_service: LLMService,
        event_log: EventLog,
        registry: CommandRegistry | None = None,
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            llm_service: LLM service for non-command input
            event_log: Structured event log
            registry: Command registry (default: create_default_registry())
        """
        self._llm_service = llm_service
        self._event_log = event_log
        self._registry = registry if registry is not None else create_default_registry()

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
            return response

        # Not a command → send to LLM
        return Response(send_to_llm=True)

    def stream_llm(self, text: str) -> Iterator[StreamEvent]:
        """Stream LLM response for the given text.

        Called by UI layer after handle_input() returns send_to_llm=True.
        Emits events for each stream phase.

        Yields:
            StreamEvent dicts for UI to render.
        """
        self._event_log.emit("llm_request_start", text=text)
        for event in self._llm_service.stream(text):
            yield event
        self._event_log.emit("llm_request_end")

    @property
    def session_id(self) -> str | None:
        """Current session ID from LLM service."""
        return self._llm_service.session_id
