"""Streaming implementation for Copilot CLI.

This module provides the streaming variant of the Copilot CLI interface,
yielding StreamEvents as each JSONL line arrives from the subprocess.
"""

import logging
import os
from collections.abc import Iterator
from typing import Any

from ....utils.executable_finder import find_executable
from ....utils.subprocess_runner import CommandOptions, CommandResult
from ....utils.subprocess_streaming import stream_subprocess
from ...types import StreamEvent
from .copilot_cli import (
    _read_settings_allow,
    build_copilot_command,
    convert_settings_to_copilot_tools,
    parse_copilot_jsonl_line,
)
from .copilot_cli_log_paths import get_stream_log_path

logger = logging.getLogger(__name__)

__all__ = [
    "ask_copilot_cli_stream",
]


def _map_copilot_message_to_event(
    msg: dict[str, Any],
) -> Iterator[StreamEvent]:
    """Map a parsed Copilot JSONL message to StreamEvent(s).

    Mapping:
    - assistant.message → text_delta (for text), tool_use_start (for toolRequests)
    - tool.execution_complete → tool_result
    - result → done (with session_id, usage)
    - session.info with unknown-tool warning → error StreamEvent + WARNING log
    - All other types → skipped (ephemeral)

    Yields:
        StreamEvent dicts corresponding to the parsed message type.
    """
    msg_type = msg.get("type", "")

    if msg_type == "assistant.message":
        data = msg.get("data", {})
        # Text content — string in real output, list in some formats
        content = data.get("content", "")
        if isinstance(content, str) and content:
            yield {"type": "text_delta", "text": content}
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("text"):
                    yield {"type": "text_delta", "text": block["text"]}
        # Tool requests
        tool_requests = data.get("toolRequests", [])
        for tool_req in tool_requests:
            if isinstance(tool_req, dict):
                yield {
                    "type": "tool_use_start",
                    "name": tool_req.get("name", ""),
                    "args": tool_req.get("args", {}),
                }

    elif msg_type == "tool.execution_complete":
        yield {
            "type": "tool_result",
            "name": msg.get("toolId", ""),
            "output": msg.get("result", ""),
        }

    elif msg_type == "result":
        usage: dict[str, object] = {}
        result_usage = msg.get("usage", {})
        if isinstance(result_usage, dict):
            if "outputTokens" in result_usage:
                usage["output_tokens"] = result_usage["outputTokens"]
            if "inputTokens" in result_usage:
                usage["input_tokens"] = result_usage["inputTokens"]
        yield {
            "type": "done",
            "session_id": msg.get("sessionId"),
            "usage": usage,
        }

    elif msg_type == "session.info":
        # Check for unknown-tool warnings
        info_data = msg.get("data", {})
        info_message = (
            info_data.get("message", "") if isinstance(info_data, dict) else ""
        )
        if isinstance(info_message, str) and "unknown tool" in info_message.lower():
            logger.warning("Copilot unknown tool warning: %s", info_message)
            yield {"type": "error", "message": info_message}


def ask_copilot_cli_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
    system_prompt: str | None = None,
    execution_dir: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream Copilot CLI responses as events.

    Same parameters as ask_copilot_cli(). Yields StreamEvent dicts
    as each JSONL line arrives from the subprocess.

    Args:
        question: The question to ask
        session_id: Optional session ID to resume
        timeout: Timeout in seconds
        env_vars: Environment variables for subprocess
        cwd: Working directory
        logs_dir: Log directory for JSONL files
        branch_name: Git branch for log filename context
        system_prompt: System prompt to prepend (skipped on resume)
        execution_dir: Directory to read .claude/settings.local.json from

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result,
        done, error, raw_line

    Raises:
        ValueError: If the question is empty/whitespace or timeout is not positive.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find executable
    copilot_cmd = find_executable(
        "copilot",
        install_hint="Install GitHub Copilot CLI: https://github.com/github/gh-copilot",
    )

    # Build prompt: prepend system prompt on new sessions only
    prompt_text = question
    if session_id is None and system_prompt:
        prompt_text = f"{system_prompt}\n\n{question}"

    # Read settings and convert to tool flags
    available_tools: list[str] | None = None
    allow_tools: list[str] | None = None
    settings_allow = _read_settings_allow(execution_dir)
    if settings_allow is not None:
        tool_flags = convert_settings_to_copilot_tools(settings_allow)
        available_tools = tool_flags["available_tools"] or None
        allow_tools = tool_flags["allow_tools"] or None

    # Build command
    command = build_copilot_command(
        prompt=prompt_text,
        copilot_cmd=copilot_cmd,
        session_id=session_id,
        available_tools=available_tools,
        allow_tools=allow_tools,
    )

    # Generate stream log file path
    stream_file = get_stream_log_path(logs_dir, cwd, branch_name)
    options = CommandOptions(
        timeout_seconds=timeout,
        env=env_vars,
        cwd=cwd,
    )

    stream = stream_subprocess(command, options, inactivity_timeout_seconds=timeout)
    try:
        log_fh = open(stream_file, "w", encoding="utf-8")  # noqa: SIM115
    except OSError:
        logger.warning(
            "Cannot open stream log %s; continuing without file logging", stream_file
        )
        log_fh = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    with log_fh as log:
        for line in stream:
            log.write(line + "\n")
            log.flush()
            yield {"type": "raw_line", "line": line}
            parsed = parse_copilot_jsonl_line(line)
            if parsed:
                yield from _map_copilot_message_to_event(parsed)

    cmd_result: CommandResult = stream.result
    if cmd_result.timed_out:
        yield {
            "type": "error",
            "message": (
                f"LLM inactivity timeout (copilot): no output for {timeout}s. "
                "Process terminated. You can retry, or use --timeout to increase the limit."
            ),
        }
    elif cmd_result.return_code != 0:
        yield {
            "type": "error",
            "message": f"CLI failed with code {cmd_result.return_code}",
        }
