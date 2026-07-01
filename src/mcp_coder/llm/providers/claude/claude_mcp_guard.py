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

# MCP server status (from the init event) that means the server is ready to use.
_MCP_SERVER_READY_STATUS = "connected"

# A server still cold-starting ("pending") is not fatal: with "ToolSearch"
# restored as the built-in wait-bridge, the model waits for it to connect within
# the same session instead of running blind. Only non-connected, non-pending
# statuses (e.g. "failed", "unknown") are terminal.
_MCP_PENDING_STATUS = "pending"


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
    servers in a **terminal** non-connected state (e.g. ``failed`` /
    ``unknown`` — a crashed or missing server that will not self-heal).
    Continuing would run the model with no tools, which can silently yield
    hallucinated results, so the call is aborted instead. A ``pending`` server
    is *not* terminal: it self-heals via ``ToolSearch`` and does not abort.

    ``unavailable_servers`` maps each fatal server name to its status.
    """

    def __init__(
        self,
        message: str,
        unavailable_servers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.unavailable_servers: dict[str, str] = unavailable_servers or {}


def _scan_mcp_servers(
    system_message: StreamMessage | None,
    *,
    tolerate_pending: bool,
) -> dict[str, str]:
    """Map non-connected server names to their status from the init event.

    Reads the ``mcp_servers`` list from the init event. Returns an empty dict
    when there is no init message or no servers were configured, so sessions
    that intentionally run without MCP are unaffected.

    Args:
        system_message: The parsed ``system``/``init`` StreamMessage, or None.
        tolerate_pending: When True, ``pending`` servers are skipped (they
            self-heal via ToolSearch); when False, every non-connected server
            is reported.

    Returns:
        Mapping of server name to lowercased status for the matching servers.
    """
    if not system_message:
        return {}
    # Typed as list[dict] but really parsed JSON; stay defensive about shape.
    servers = cast(list[Any], system_message.get("mcp_servers") or [])
    result: dict[str, str] = {}
    for server in servers:
        if not isinstance(server, dict):
            continue
        status = str(server.get("status", "")).strip().lower() or "unknown"
        if status == _MCP_SERVER_READY_STATUS:
            continue
        if tolerate_pending and status == _MCP_PENDING_STATUS:
            continue
        result[str(server.get("name", "?"))] = status
    return result


def find_unavailable_mcp_servers(
    system_message: StreamMessage | None,
) -> dict[str, str]:
    """Return ``{name: status}`` for configured MCP servers that aren't ready.

    Reports every server whose status is not ``connected`` (including
    ``pending``), so still-starting servers can be surfaced in logs.

    Args:
        system_message: The parsed ``system``/``init`` StreamMessage, or None.

    Returns:
        Mapping of server name to lowercased status for servers whose status is
        not ``connected``; empty when all are ready (or none configured).
    """
    return _scan_mcp_servers(system_message, tolerate_pending=False)


def find_fatal_mcp_servers(
    system_message: StreamMessage | None,
) -> dict[str, str]:
    """Return ``{name: status}`` for servers in a terminal non-connected state.

    Like :func:`find_unavailable_mcp_servers` but tolerates ``pending``: a
    still-starting server self-heals via ``ToolSearch`` within the session, so
    it is not reported. Only terminal statuses (e.g. ``failed`` / ``unknown``)
    appear here, identifying servers that warrant aborting the run.

    Args:
        system_message: The parsed ``system``/``init`` StreamMessage, or None.

    Returns:
        Mapping of server name to lowercased status for servers whose status is
        neither ``connected`` nor ``pending``; empty otherwise.
    """
    return _scan_mcp_servers(system_message, tolerate_pending=True)


# Prefix identifying MCP tools in the init event's ``tools`` field. Built-in
# tools (e.g. ``ToolSearch``, ``Bash``) do not carry this prefix.
_MCP_TOOL_PREFIX = "mcp__"


def find_exposed_mcp_tools(system_message: StreamMessage | None) -> list[str]:
    """Return sorted, de-duplicated ``mcp__*`` tool names from the init event.

    Reads the init event's ``tools`` field (the list of tools actually exposed
    to the model) and keeps only MCP tools (names starting with ``mcp__``).
    Built-in tools (e.g. ``ToolSearch``) are excluded. Returns ``[]`` when the
    message is ``None``, has no ``tools`` field, or exposed no MCP tools — so a
    healthy-but-toolless session is represented as an empty list, not an error.

    Args:
        system_message: The parsed ``system``/``init`` StreamMessage, or None.

    Returns:
        Sorted list of unique ``mcp__*`` tool names; empty when none exposed.
    """
    if system_message is None:
        return []
    # Really parsed JSON; stay defensive about shape: entries may be plain
    # strings or dicts carrying a ``name`` field.
    tools = system_message.get("tools") or []
    names: set[str] = set()
    for tool in tools:
        if isinstance(tool, str):
            name: str | None = tool
        elif isinstance(tool, dict):
            raw = tool.get("name")
            name = raw if isinstance(raw, str) else None
        else:
            name = None
        if name is not None and name.startswith(_MCP_TOOL_PREFIX):
            names.add(name)
    return sorted(names)


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
