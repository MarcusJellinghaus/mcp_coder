#!/usr/bin/env python3
"""Stream-json parsing and the MCP-availability guard for Claude Code CLI.

Extracted from ``claude_code_cli.py`` to keep file sizes manageable. This
module owns the machinery that turns Claude CLI stream-json (NDJSON) output
into structured responses, plus the guard that aborts a session when its
configured MCP servers did not connect.

``claude_code_cli.py`` re-exports every public name here, so importers can
continue to import these from either location.
"""

import json
import logging
from pathlib import Path
from typing import Any, TypedDict, cast

logger = logging.getLogger(__name__)

# MCP cold-start retry: a server reported "pending" at init is usually still
# starting (common when sessions contend for CPU/disk under parallel load). A
# fresh attempt with a warm OS cache normally connects, so retry a bounded
# number of times before giving up. Terminal failures ("failed") are not retried.
MCP_UNAVAILABLE_MAX_RETRIES = 2  # extra attempts after the first (3 total)
MCP_UNAVAILABLE_RETRY_WAIT_SECONDS = 5.0

# MCP server status (from the init event) that means the server is ready to use.
_MCP_SERVER_READY_STATUS = "connected"

# Statuses worth retrying: a server still cold-starting ("pending") usually
# connects on a fresh attempt with a warm cache. Anything else (e.g. "failed",
# "unknown") is treated as terminal — a retry won't fix it.
_MCP_RETRYABLE_STATUSES = frozenset({"pending"})


class StreamMessage(TypedDict, total=False):
    """A single message from Claude CLI stream-json output."""

    type: str
    subtype: str
    session_id: str
    message: dict[str, Any]
    result: str
    is_error: bool
    total_cost_usd: float
    duration_ms: int
    usage: dict[str, Any]
    tools: list[Any]
    mcp_servers: list[dict[str, Any]]


class ParsedStreamResponse(TypedDict):
    """Parsed stream-json response with all messages."""

    text: str
    session_id: str | None
    messages: list[StreamMessage]
    result_message: StreamMessage | None
    system_message: StreamMessage | None


class McpServersUnavailableError(RuntimeError):
    """Raised when a Claude session starts without its configured MCP servers.

    The session's ``system``/``init`` event reported one or more configured MCP
    servers that did not reach ``connected`` status (e.g. ``failed`` /
    ``pending``). Continuing would run the model with no tools, which can
    silently yield hallucinated results, so the call is aborted instead.

    ``unavailable_servers`` carries the ``(name, status)`` pairs so callers can
    decide whether to retry (see :func:`mcp_failure_is_retryable`).
    """

    def __init__(
        self,
        message: str,
        unavailable_servers: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.unavailable_servers: list[tuple[str, str]] = unavailable_servers or []


def find_unavailable_mcp_servers(
    system_message: StreamMessage | None,
) -> list[tuple[str, str]]:
    """Return ``(name, status)`` for configured MCP servers that aren't ready.

    Reads the ``mcp_servers`` list from the init event. Returns an empty list
    when there is no init message or no servers were configured, so sessions
    that intentionally run without MCP are unaffected.

    Args:
        system_message: The parsed ``system``/``init`` StreamMessage, or None.

    Returns:
        List of ``(name, status)`` tuples for servers whose status is not
        ``connected``; empty when all servers are ready (or none configured).
    """
    if not system_message:
        return []
    # Typed as list[dict] but really parsed JSON; stay defensive about shape.
    servers = cast(list[Any], system_message.get("mcp_servers") or [])
    unavailable: list[tuple[str, str]] = []
    for server in servers:
        if not isinstance(server, dict):
            continue
        status = str(server.get("status", "")).strip().lower()
        if status != _MCP_SERVER_READY_STATUS:
            unavailable.append((str(server.get("name", "?")), status or "unknown"))
    return unavailable


def mcp_failure_is_retryable(unavailable_servers: list[tuple[str, str]]) -> bool:
    """Return True when every unavailable server is in a transient state.

    ``pending`` means a server is still cold-starting (common when several
    sessions start at once and contend for CPU/disk); a fresh attempt with a
    warm cache usually connects. A terminal status (``failed`` / ``unknown``,
    e.g. a missing executable or a crash) is not worth retrying.
    """
    if not unavailable_servers:
        return False
    return all(
        status in _MCP_RETRYABLE_STATUSES for _name, status in unavailable_servers
    )


def parse_stream_json_line(line: str) -> StreamMessage | None:
    """Parse a single line of stream-json output.

    Args:
        line: A single line from stream-json output

    Returns:
        Parsed StreamMessage or None if line is empty/invalid
    """
    line = line.strip()
    if not line:
        return None

    try:
        parsed = json.loads(line)
        return cast(StreamMessage, parsed)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse stream line: {e}")
        return None


def _parse_stream_lines(lines: list[str]) -> ParsedStreamResponse:
    """Parse stream-json lines into structured response (internal helper).

    Args:
        lines: List of NDJSON lines to parse

    Returns:
        ParsedStreamResponse with extracted text, session_id, and all messages
    """
    messages: list[StreamMessage] = []
    text_parts: list[str] = []
    session_id: str | None = None
    result_message: StreamMessage | None = None
    system_message: StreamMessage | None = None

    for line in lines:
        msg = parse_stream_json_line(line)
        if msg is None:
            continue

        messages.append(msg)
        msg_type = msg.get("type", "")

        # Extract session_id from system init or result messages
        if "session_id" in msg:
            session_id = msg["session_id"]

        # Handle different message types
        if msg_type == "system":
            # Keep the init event specifically. Later `system` events (e.g.
            # `thinking_tokens` heartbeats emitted during extended thinking) must
            # NOT overwrite it, or the MCP-availability guard would read a
            # message with no `mcp_servers` field and miss a failed startup. (#998)
            if msg.get("subtype") == "init" or system_message is None:
                system_message = msg
        elif msg_type == "assistant":
            # Extract text from assistant message content blocks
            message_data = msg.get("message", {})
            content_blocks = message_data.get("content", [])
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
        elif msg_type == "result":
            result_message = msg
            # Result message also contains the final text
            if "result" in msg:
                # Only use result text if we didn't get text from assistant messages
                if not text_parts:
                    text_parts.append(str(msg["result"]))

    return ParsedStreamResponse(
        text="".join(text_parts).strip(),
        session_id=session_id,
        messages=messages,
        result_message=result_message,
        system_message=system_message,
    )


def parse_stream_json_file(file_path: Path) -> ParsedStreamResponse:
    """Parse a stream-json log file into structured response.

    Args:
        file_path: Path to the NDJSON stream log file

    Returns:
        ParsedStreamResponse with extracted text, session_id, and all messages
    """
    if not file_path.exists():
        return ParsedStreamResponse(
            text="",
            session_id=None,
            messages=[],
            result_message=None,
            system_message=None,
        )

    try:
        content = file_path.read_text(encoding="utf-8")
        return _parse_stream_lines(content.splitlines())
    except (OSError, IOError) as e:
        logger.error(f"Failed to read stream file {file_path}: {e}")
        return ParsedStreamResponse(
            text="",
            session_id=None,
            messages=[],
            result_message=None,
            system_message=None,
        )


def parse_stream_json_string(content: str) -> ParsedStreamResponse:
    """Parse stream-json content from a string.

    Args:
        content: NDJSON content as a string

    Returns:
        ParsedStreamResponse with extracted data
    """
    return _parse_stream_lines(content.splitlines())
