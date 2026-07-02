"""Streaming implementation for Claude Code CLI.

This module provides the streaming variant of the Claude Code CLI interface,
yielding StreamEvents as each NDJSON line arrives from the subprocess.

Extracted from claude_code_cli.py to keep file sizes manageable.
"""

import logging
import os
from collections.abc import Iterator

from ....utils.subprocess_runner import CommandOptions, CommandResult
from ....utils.subprocess_streaming import stream_subprocess
from ...types import StreamEvent
from .claude_code_cli import (
    _find_claude_executable,
    build_cli_command,
    format_stream_json_input,
)
from .claude_code_cli_log_paths import get_stream_log_path
from .claude_mcp_guard import (
    McpServersUnavailableError,
    StreamMessage,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
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
                    "is_error": block.get("is_error", False),
                }
    elif msg_type == "result":
        yield {
            "type": "done",
            "session_id": msg.get("session_id"),
            "usage": msg.get("usage", {}),
            "cost_usd": msg.get("total_cost_usd"),
            # Carry the final result text so the assembler can reproduce the
            # blocking-path fallback (used only when no assistant text is seen).
            "result": msg.get("result"),
        }


def ask_claude_code_cli_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
    append_system_prompt: str | None = None,
    system_prompt_replace: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream Claude CLI responses as events.

    Same parameters as ask_claude_code_cli(). Instead of returning a single
    LLMResponseDict, yields StreamEvent dicts as each NDJSON line arrives
    from the Claude CLI subprocess.

    The ``settings_file`` parameter, when provided, is forwarded via ``--settings``
    to override matching keys in cwd-discovered Claude settings for the session.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error,
        raw_line, system (the init message payload)

    Raises:
        ValueError: If the question is empty/whitespace or timeout is not positive.
        McpServersUnavailableError: If the init event reports a configured MCP
            server that did not reach ``connected`` status; aborted before any
            assistant content is yielded.

    The "done" event includes session_id and usage data from the result message.
    The "raw_line" event wraps each raw NDJSON line for json-raw mode consumers.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    claude_cmd = _find_claude_executable()
    command = build_cli_command(
        session_id,
        claude_cmd,
        mcp_config,
        use_stream_json=True,
        append_system_prompt=append_system_prompt,
        system_prompt_replace=system_prompt_replace,
        settings_file=settings_file,
    )
    stream_file = get_stream_log_path(logs_dir, cwd, branch_name)
    # Announce the stream log path up front so consumers (e.g. the drain-wrapper)
    # can capture it before any subprocess output arrives.
    yield {"type": "stream_file", "path": str(stream_file)}
    input_data = format_stream_json_input(question)
    options = CommandOptions(
        input_data=input_data,
        env=env_vars,
        cwd=cwd,
        env_remove=["CLAUDECODE"],  # Allow nested Claude CLI invocations
    )

    stream = stream_subprocess(command, options, inactivity_timeout_seconds=timeout)
    try:
        log_fh = open(stream_file, "w", encoding="utf-8")  # noqa: SIM115
    except OSError:
        logger.warning(
            "Cannot open stream log %s; continuing without file logging", stream_file
        )
        log_fh = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    saw_system_init = False
    with log_fh as log:
        for line in stream:
            log.write(line + "\n")
            log.flush()
            yield {"type": "raw_line", "line": line}
            msg = parse_stream_json_line(line)
            if not msg:
                continue
            if msg.get("type") == "system":
                # Surface the init/system message to the assembler so the
                # blocking path can repopulate raw_response["system"] (parity
                # with main). Keep only the init event: later `system` heartbeats
                # (e.g. thinking_tokens) carry no mcp_servers/tools and must not
                # overwrite it, matching _parse_stream_lines. (#998, #1004)
                if msg.get("subtype") == "init" or not saw_system_init:
                    saw_system_init = True
                    yield {"type": "system", "data": dict(msg)}
                # MCP availability guard (matches the blocking path). Abort only
                # on fatal (terminal, non-pending) servers so the model never
                # runs blind on hallucinated tools. Pending servers self-heal
                # within the session via the ToolSearch wait-bridge, so they are
                # tolerated and only logged.
                fatal_servers = find_fatal_mcp_servers(msg)
                if fatal_servers:
                    detail = ", ".join(
                        f"{name}={status}" for name, status in fatal_servers.items()
                    )
                    mcp_error_msg = (
                        f"MCP servers not available: {detail}. The session started "
                        f"without its configured tools; aborting before the model "
                        f"runs blind. Stream log: {stream_file}"
                    )
                    logger.error(mcp_error_msg)
                    raise McpServersUnavailableError(
                        mcp_error_msg, unavailable_servers=fatal_servers
                    )

                # Fatal servers already aborted above, so any remaining
                # non-connected servers are pending.
                pending_servers = find_unavailable_mcp_servers(msg)
                if pending_servers:
                    logger.info(
                        "MCP server(s) still starting; ToolSearch will wait: %s",
                        pending_servers,
                    )
            yield from _map_stream_message_to_event(msg)

    cmd_result: CommandResult = stream.result
    if cmd_result.timed_out:
        yield {
            "type": "error",
            "reason": "inactivity_timeout",
            "timeout": timeout,
            "message": (
                f"LLM inactivity timeout (claude): no output for {timeout}s. "
                "Process terminated. You can retry, or use --timeout to increase the limit."
            ),
        }
    elif cmd_result.return_code != 0:
        error_msg = f"CLI failed with code {cmd_result.return_code}"
        if cmd_result.stderr:
            error_msg += f": {cmd_result.stderr[:500]}"
        yield {
            "type": "error",
            "reason": "nonzero_exit",
            "return_code": cmd_result.return_code,
            "message": error_msg,
        }
