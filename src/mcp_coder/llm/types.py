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
    "SUPPORTED_PROVIDERS",
    "UsageInfo",
]


SUPPORTED_PROVIDERS: frozenset[str] = frozenset({"claude", "langchain", "copilot"})


class UsageInfo(TypedDict, total=False):
    """Provider-agnostic token usage. All fields optional (total=False)."""

    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int


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
- {"type": "tool_result", "name": "...", "output": "...", "is_error": bool} — tool
  call result; the optional ``is_error`` flag (default ``False`` when absent)
  signals the tool reported a failure
- {"type": "error", "message": "...", "reason": "..."} — error during stream; the
  optional ``reason`` discriminator (e.g. ``"inactivity_timeout"``, ``"nonzero_exit"``)
  lets consumers translate the failure without string-matching the message
- {"type": "done", "usage": {...}, "result": "..."} — stream complete with optional
  usage stats and the final result text
- {"type": "raw_line", "line": "..."} — raw NDJSON line passthrough (json-raw mode)
- {"type": "stream_file", "path": "..."} — announces the NDJSON stream log path
- {"type": "system", "data": {...}} — the Claude CLI init/system message dict
  (carries ``mcp_servers``/``tools``); surfaced so blocking consumers can read
  ``raw_response["system"]``
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
        self._stream_file: str | None = None
        self._system: object | None = None
        self._saw_assistant_text: bool = False
        self._result_text: str | None = None

    def add(self, event: StreamEvent) -> None:
        """Process a single stream event, accumulating text and metadata."""
        event_type = event.get("type")
        # `raw_line` events duplicate the parsed events and are already persisted
        # separately in `stream_file`; keep them out of the assembled `events`
        # list to avoid ~2x payload. Live consumers still receive them from the
        # generator directly.
        if event_type != "raw_line":
            self._raw_events.append(event)
        if event_type == "text_delta":
            self._saw_assistant_text = True
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
            result_text = event.get("result")
            if isinstance(result_text, str):
                self._result_text = result_text
        elif event_type == "stream_file":
            path = event.get("path")
            if isinstance(path, str):
                self._stream_file = path
        elif event_type == "system":
            # The Claude init message payload; kept so the blocking path can
            # repopulate raw_response["system"] (parity with main), which the
            # MCP-guard consumers (env_setup, verify) read.
            self._system = event.get("data")
        elif event_type in ("tool_use_start", "tool_result"):
            self._tool_trace.append(event)
        elif event_type == "error":
            message = event.get("message")
            if isinstance(message, str):
                self._error = message

    @property
    def has_error(self) -> bool:
        """Whether an error event was received during streaming."""
        return self._error is not None

    def result(self) -> LLMResponseDict:
        """Build and return the final LLMResponseDict from accumulated events.

        Returns:
            LLMResponseDict with text, session info, and raw events.
        """
        raw_response: dict[str, object] = {"events": list(self._raw_events)}
        if self._stream_file is not None:
            raw_response["stream_file"] = self._stream_file
        if self._system is not None:
            raw_response["system"] = self._system
        if self._usage:
            raw_response["usage"] = self._usage
        if self._tool_trace:
            raw_response["tool_trace"] = list(self._tool_trace)
        if self._error is not None:
            raw_response["error"] = self._error
        # Text parity (AC3) with the blocking _parse_stream_lines output: strip the
        # concatenated assistant text, and fall back to the result-message `result`
        # value only when no assistant-text event was seen.
        text = "".join(self._text_parts).strip()
        if not self._saw_assistant_text and self._result_text is not None:
            text = self._result_text.strip()
        return LLMResponseDict(
            version=LLM_RESPONSE_VERSION,
            timestamp=datetime.now().isoformat(),
            text=text,
            session_id=self._session_id,
            provider=self._provider,
            raw_response=raw_response,
        )
