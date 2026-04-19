"""Copilot CLI JSONL parser, tool permission converter, and command builder.

Provides pure parsing functions for Copilot CLI JSONL output,
conversion of settings.local.json permission entries to Copilot CLI flags,
and the main ask_copilot_cli() entry point.
"""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from ....utils.executable_finder import find_executable
from ....utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    TimeoutExpired,
    execute_subprocess,
)
from ...logging_utils import log_llm_error, log_llm_request, log_llm_response
from ...types import LLM_RESPONSE_VERSION, LLMResponseDict
from .copilot_cli_log_paths import get_stream_log_path

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

    Returns:
        Parsed dict or None if line is empty/invalid.
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

    Returns:
        ParsedCopilotResponse with text, session_id, messages, usage, and raw_result.
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


# Windows CreateProcess limit for .CMD wrappers
COPILOT_CMD_LINE_LIMIT = 8192


def build_copilot_command(
    prompt: str,
    copilot_cmd: str,
    session_id: str | None = None,
    available_tools: list[str] | None = None,
    allow_tools: list[str] | None = None,
) -> list[str]:
    """Build Copilot CLI command arguments.

    Always includes: -p, --output-format json, -s, --allow-all-tools
    Conditionally: --available-tools, --allow-tool (per entry), --resume

    Args:
        prompt: User prompt text (passed via -p)
        copilot_cmd: Path to copilot executable
        session_id: Optional session ID for --resume
        available_tools: Flat hyphen format tool names for --available-tools
        allow_tools: Parentheses format entries for --allow-tool (one flag per entry)

    Returns:
        Command list ready for subprocess execution.

    Raises:
        ValueError: If copilot_cmd is empty, or if combined command exceeds 8KB.
    """
    if not copilot_cmd or not copilot_cmd.strip():
        raise ValueError("copilot_cmd cannot be empty")

    command = [
        copilot_cmd,
        "-p",
        prompt,
        "--output-format",
        "json",
        "-s",
        # --allow-all-tools auto-approves visible tools without prompting;
        # --available-tools (added below) controls which tools are visible.
        # They are complementary, not redundant.
        "--allow-all-tools",
    ]

    if available_tools:
        command.append(f"--available-tools={','.join(available_tools)}")

    if allow_tools:
        for tool_entry in allow_tools:
            command.append(f"--allow-tool={tool_entry}")

    if session_id:
        command.append(f"--resume={session_id}")

    # Check total command line length (Windows CreateProcess limit)
    cmd_line_length = len(" ".join(command))
    if cmd_line_length > COPILOT_CMD_LINE_LIMIT:
        raise ValueError(
            f"Command line length ({cmd_line_length} chars) exceeds "
            f"{COPILOT_CMD_LINE_LIMIT} char limit. "
            f"Reduce the number of --available-tools or --allow-tool entries."
        )

    return command


def _read_settings_allow(execution_dir: str | None) -> list[str] | None:
    """Read permissions.allow from .claude/settings.local.json.

    Returns:
        List of allow entries, or None if file not found.
    """
    if execution_dir:
        base_dir = Path(execution_dir)
    else:
        base_dir = Path.cwd()

    settings_path = base_dir / ".claude" / "settings.local.json"
    if not settings_path.exists():
        return None

    try:
        content = settings_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except (OSError, json.JSONDecodeError):
        return None

    permissions = data.get("permissions")
    if not isinstance(permissions, dict):
        return None

    allow = permissions.get("allow")
    if not isinstance(allow, list):
        return None

    return allow


def ask_copilot_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
    system_prompt: str | None = None,
    execution_dir: str | None = None,
) -> LLMResponseDict:
    """Ask Copilot CLI with session support and JSONL logging.

    Args:
        question: The question to ask
        session_id: Optional session ID to resume (skips system_prompt if set)
        timeout: Timeout in seconds
        env_vars: Environment variables for subprocess
        cwd: Working directory (Copilot discovers .mcp.json from here)
        logs_dir: Log directory for JSONL files
        branch_name: Git branch for log filename context
        system_prompt: System prompt to prepend to question (skipped on resume)
        execution_dir: Directory to read .claude/settings.local.json from

    Returns:
        LLMResponseDict with text, session_id, provider="copilot", raw_response

    Raises:
        ValueError: If question is empty or command exceeds 8KB
        TimeoutExpired: If command times out
        CalledProcessError: If command fails
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find executable
    copilot_cmd = find_executable(
        "copilot",
        install_hint="Install GitHub Copilot CLI: https://github.com/github/gh-copilot",
    )

    # Build prompt: prepend system prompt on new sessions only.
    # Workaround: Copilot CLI has no --system-prompt flag, so we prepend
    # it to the user question. On --resume we skip it because Copilot
    # preserves full conversation history and would duplicate it.
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
    stream_file_path = get_stream_log_path(logs_dir, cwd, branch_name)
    stream_file_str = str(stream_file_path)
    logger.debug("Stream log file: %s", stream_file_str)

    # Log request
    log_llm_request(
        provider="copilot",
        session_id=session_id,
        prompt=question,
        timeout=timeout,
        env_vars=env_vars or {},
        cwd=cwd or "",
        command=command,
    )

    # Execute subprocess
    start_time = time.time()
    options = CommandOptions(
        timeout_seconds=timeout,
        env=env_vars,
        cwd=cwd,
    )

    try:
        result = execute_subprocess(command, options)

        # Save stdout to JSONL log file
        if result.stdout:
            try:
                stream_file_path.write_text(result.stdout, encoding="utf-8")
            except OSError as e:
                logger.warning("Failed to write stream file: %s", e)

        # Handle errors
        if result.timed_out:
            duration_ms = int((time.time() - start_time) * 1000)
            timeout_error: Exception = TimeoutExpired(command, timeout)
            log_llm_error(error=timeout_error, duration_ms=duration_ms)
            raise timeout_error

        if result.return_code != 0:
            duration_ms = int((time.time() - start_time) * 1000)
            called_process_error = CalledProcessError(
                result.return_code,
                command,
                output=result.stdout,
                stderr=(
                    f"{result.stderr}\nStream file: {stream_file_str}"
                    if result.stderr
                    else f"Stream file: {stream_file_str}"
                ),
            )
            log_llm_error(error=called_process_error, duration_ms=duration_ms)
            raise called_process_error

        # Parse output
        lines = result.stdout.splitlines() if result.stdout else []
        parsed = parse_copilot_jsonl_output(lines)

        # Log response
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_response(
            duration_ms=duration_ms,
            session_id=parsed["session_id"],
        )

        # Build raw_response
        raw_response: dict[str, object] = {
            "messages": parsed["messages"],
            "stream_file": stream_file_str,
        }
        if parsed["usage"]:
            raw_response["usage"] = parsed["usage"]
        if parsed["raw_result"]:
            raw_response["sessionId"] = parsed["raw_result"].get("sessionId")
            raw_response["premiumRequests"] = parsed["raw_result"].get(
                "premiumRequests"
            )

        return LLMResponseDict(
            version=LLM_RESPONSE_VERSION,
            timestamp=datetime.now().isoformat(),
            text=parsed["text"],
            session_id=parsed["session_id"],
            provider="copilot",
            raw_response=raw_response,
        )

    except (TimeoutExpired, CalledProcessError, ValueError):
        raise
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(error=e, duration_ms=duration_ms)
        raise
