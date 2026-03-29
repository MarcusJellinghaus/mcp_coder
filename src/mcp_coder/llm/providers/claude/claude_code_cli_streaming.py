"""Streaming implementation for Claude Code CLI.

This module provides the streaming variant of the Claude Code CLI interface,
yielding StreamEvents as each NDJSON line arrives from the subprocess.

Extracted from claude_code_cli.py to keep file sizes manageable.
"""

import logging
import os
from collections.abc import Iterator

from ....utils.subprocess_runner import CommandOptions, CommandResult
from ....utils.subprocess_streaming import StreamResult, stream_subprocess
from ...types import StreamEvent
from .claude_code_cli import (
    StreamMessage,
    _find_claude_executable,
    build_cli_command,
    format_stream_json_input,
    get_stream_log_path,
    parse_stream_json_line,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ask_claude_code_cli_stream",
]


def _map_stream_message_to_event(msg: StreamMessage) -> Iterator[StreamEvent]:
    """Map a parsed StreamMessage to zero or more StreamEvents.

    Args:
        msg: Parsed NDJSON message from Claude CLI.

    Yields:
        StreamEvent dicts derived from the message content blocks.
    """
    msg_type = msg.get("type", "")

    if msg_type == "assistant":
        message_data = msg.get("message", {})
        content_blocks = message_data.get("content", [])
        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                yield {"type": "text_delta", "text": block.get("text", "")}
            elif block_type == "tool_use":
                yield {
                    "type": "tool_use_start",
                    "name": block.get("name", ""),
                    "args": block.get("input", {}),
                }
            elif block_type == "tool_result":
                yield {
                    "type": "tool_result",
                    "name": block.get("name", ""),
                    "output": block.get("content", ""),
                }
    elif msg_type == "result":
        yield {
            "type": "done",
            "session_id": msg.get("session_id"),
            "usage": msg.get("usage", {}),
            "cost_usd": msg.get("total_cost_usd"),
        }


def ask_claude_code_cli_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    mcp_config: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream Claude CLI responses as events.

    Same parameters as ask_claude_code_cli(). Instead of returning a single
    LLMResponseDict, yields StreamEvent dicts as each NDJSON line arrives
    from the Claude CLI subprocess.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error, raw_line

    Raises:
        ValueError: If the question is empty/whitespace or timeout is not positive.

    The "done" event includes session_id and usage data from the result message.
    The "raw_line" event wraps each raw NDJSON line for json-raw mode consumers.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    claude_cmd = _find_claude_executable()
    command = build_cli_command(
        session_id, claude_cmd, mcp_config, use_stream_json=True
    )
    stream_file = get_stream_log_path(logs_dir, cwd, branch_name)
    input_data = format_stream_json_input(question)
    options = CommandOptions(
        timeout_seconds=timeout,
        input_data=input_data,
        env=env_vars,
        cwd=cwd,
        env_remove=["CLAUDECODE"],  # Allow nested Claude CLI invocations
    )

    stream = StreamResult(stream_subprocess(command, options))
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
            msg = parse_stream_json_line(line)
            if msg:
                yield from _map_stream_message_to_event(msg)

    # pylint: disable=no-member  # StreamResult.result is typed CommandResult
    cmd_result: CommandResult = stream.result
    if cmd_result.timed_out:
        yield {"type": "error", "message": f"Timed out after {timeout}s"}
    if cmd_result.return_code != 0:
        yield {
            "type": "error",
            "message": f"CLI failed with code {cmd_result.return_code}",
        }
