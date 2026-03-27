"""Type definitions for LLM responses and serialization.

This module provides TypedDict definitions and constants for structured
LLM responses with session management and versioned serialization support.
"""

from datetime import datetime
from typing import TypedDict

__all__ = [
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
    "ResponseAssembler",
    "StreamEvent",
]


class LLMResponseDict(TypedDict):
    """Structured LLM response with session and serialization support.

    This TypedDict defines the complete structure for LLM responses that include
    session management, timestamps, and raw response data for comprehensive logging.

    Attributes:
        version: Serialization format version (e.g., "1.0")
        timestamp: ISO format timestamp when response was created
        text: The actual text response from the LLM
        session_id: Unique session identifier for conversation continuity.
                   None if session ID is not available or not provided by LLM.
        provider: LLM provider name (e.g., "claude", "langchain")
        raw_response: Complete unmodified response data from CLI JSON or API
                     This preserves all metadata, usage stats, and provider-specific
                     information for future analysis and parsing

    Example:
        {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00.123456",
            "text": "Python is a programming language...",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "provider": "claude",
            "raw_response": {
                "duration_ms": 2801,
                "cost_usd": 0.058,
                ...
            }
        }
    """

    version: str
    timestamp: str
    text: str
    session_id: str | None
    provider: str
    raw_response: dict[str, object]


# Current serialization version
# Version numbering:
# - Major version (X.0): Breaking changes to structure
# - Minor version (1.X): Backward-compatible additions
LLM_RESPONSE_VERSION = "1.0"

StreamEvent = dict[str, object]
"""Stream event dict. Always has a "type" key. Known types:

- {"type": "text_delta", "text": "..."} — incremental text token
- {"type": "tool_use_start", "name": "...", "args": {...}} — tool call begins
- {"type": "tool_result", "name": "...", "output": "..."} — tool call result
- {"type": "error", "message": "..."} — error during stream
- {"type": "done", "usage": {...}} — stream complete with optional usage stats
- {"type": "raw_line", "line": "..."} — raw NDJSON line passthrough (json-raw mode)
"""


class ResponseAssembler:
    """Accumulates StreamEvents into a complete LLMResponseDict."""

    def __init__(self, provider: str) -> None:
        """Initialize assembler for given provider name."""
        self._provider = provider
        self._text_parts: list[str] = []
        self._session_id: str | None = None
        self._usage: dict[str, object] = {}
        self._raw_events: list[StreamEvent] = []
        self._tool_trace: list[StreamEvent] = []
        self._error: str | None = None

    def add(self, event: StreamEvent) -> None:
        """Process a single stream event, accumulating text and metadata."""
        self._raw_events.append(event)
        event_type = event.get("type")
        if event_type == "text_delta":
            text = event.get("text", "")
            if isinstance(text, str):
                self._text_parts.append(text)
        elif event_type == "done":
            usage = event.get("usage")
            if isinstance(usage, dict):
                self._usage = usage
            session_id = event.get("session_id")
            if isinstance(session_id, str):
                self._session_id = session_id
        elif event_type in ("tool_use_start", "tool_result"):
            self._tool_trace.append(event)
        elif event_type == "error":
            message = event.get("message")
            if isinstance(message, str):
                self._error = message

    def result(self) -> LLMResponseDict:
        """Build and return the final LLMResponseDict from accumulated events.

        Returns:
            LLMResponseDict with text, session info, and raw events.
        """
        raw_response: dict[str, object] = {"events": list(self._raw_events)}
        if self._usage:
            raw_response["usage"] = self._usage
        if self._tool_trace:
            raw_response["tool_trace"] = list(self._tool_trace)
        if self._error is not None:
            raw_response["error"] = self._error
        return LLMResponseDict(
            version=LLM_RESPONSE_VERSION,
            timestamp=datetime.now().isoformat(),
            text="".join(self._text_parts),
            session_id=self._session_id,
            provider=self._provider,
            raw_response=raw_response,
        )
