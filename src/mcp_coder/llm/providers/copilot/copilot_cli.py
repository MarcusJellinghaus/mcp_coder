"""Copilot CLI JSONL parser and tool permission converter.

Provides pure parsing functions for Copilot CLI JSONL output and
conversion of settings.local.json permission entries to Copilot CLI flags.
"""

import json
import logging
import re
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class ParsedCopilotResponse(TypedDict):
    """Parsed response from Copilot CLI JSONL output."""

    text: str
    session_id: str | None
    messages: list[dict[str, Any]]
    usage: dict[str, object]
    raw_result: dict[str, Any] | None


class CopilotToolFlags(TypedDict):
    """Copilot CLI tool flag values."""

    available_tools: list[str]
    allow_tools: list[str]


def parse_copilot_jsonl_line(line: str) -> dict[str, Any] | None:
    """Parse a single JSONL line from Copilot output.

    Returns parsed dict or None if line is empty/invalid.
    """
    stripped = line.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, ValueError):
        return None


def parse_copilot_jsonl_output(lines: list[str]) -> ParsedCopilotResponse:
    """Parse complete Copilot JSONL output into structured response.

    Extracts:
    - text from assistant.message content blocks
    - session_id from result message's sessionId field
    - usage: outputTokens → output_tokens mapping
    - Copilot-specific fields into raw_response
    """
    text_parts: list[str] = []
    messages: list[dict[str, Any]] = []
    session_id: str | None = None
    usage: dict[str, object] = {}
    raw_result: dict[str, Any] | None = None

    for line in lines:
        parsed = parse_copilot_jsonl_line(line)
        if parsed is None:
            continue

        messages.append(parsed)
        msg_type = parsed.get("type", "")

        if msg_type == "assistant.message":
            message = parsed.get("message", {})
            content_blocks = message.get("content", [])
            for block in content_blocks:
                if isinstance(block, dict) and block.get("text"):
                    text_parts.append(block["text"])

        elif msg_type == "result":
            raw_result = parsed
            result_session_id = parsed.get("sessionId")
            if result_session_id:
                session_id = result_session_id
            result_usage = parsed.get("usage", {})
            if isinstance(result_usage, dict):
                if "outputTokens" in result_usage:
                    usage["output_tokens"] = result_usage["outputTokens"]
                if "inputTokens" in result_usage:
                    usage["input_tokens"] = result_usage["inputTokens"]

    return ParsedCopilotResponse(
        text="\n".join(text_parts) if text_parts else "",
        session_id=session_id,
        messages=messages,
        usage=usage,
        raw_result=raw_result,
    )


_MCP_PATTERN = re.compile(r"^mcp__(.+?)__(.+)$")


def convert_settings_to_copilot_tools(
    allow_entries: list[str],
) -> CopilotToolFlags:
    """Convert .claude/settings.local.json permission entries to Copilot CLI flags.

    Mapping rules:
    - mcp__<server>__<tool> → <server>-<tool> (for --available-tools)
    - Bash(<cmd>:<pattern>) → shell(<cmd>:<pattern>) (for --allow-tool)
    - Skill(...), WebFetch(...) → skipped with warning

    Args:
        allow_entries: List of permission strings from settings.local.json

    Returns:
        CopilotToolFlags with two lists of flag values.
    """
    available_tools: list[str] = []
    allow_tools: list[str] = []

    for entry in allow_entries:
        mcp_match = _MCP_PATTERN.match(entry)
        if mcp_match:
            server = mcp_match.group(1)
            tool = mcp_match.group(2)
            available_tools.append(f"{server}-{tool}")
        elif entry.startswith("Bash("):
            converted = "shell(" + entry[5:]
            allow_tools.append(converted)
        elif entry.startswith("Skill("):
            logger.warning("Skipping unmappable permission entry: %s", entry)
        elif entry.startswith("WebFetch("):
            logger.warning("Skipping unmappable permission entry: %s", entry)
        else:
            logger.warning("Skipping unknown permission format: %s", entry)

    return CopilotToolFlags(
        available_tools=available_tools,
        allow_tools=allow_tools,
    )
