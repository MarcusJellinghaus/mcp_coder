#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

from ....utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    CommandResult,
    TimeoutExpired,
    execute_subprocess,
)
from ...logging_utils import log_llm_error, log_llm_request, log_llm_response
from ...types import LLM_RESPONSE_VERSION, LLMResponseDict
from .claude_code_cli_log_paths import get_stream_log_path, sanitize_branch_identifier
from .claude_executable_finder import find_claude_executable

logger = logging.getLogger(__name__)

# Heartbeat interval for LLM subprocess calls (2 minutes)
LLM_HEARTBEAT_INTERVAL_SECONDS = 120

# MCP cold-start retry: a server reported "pending" at init is usually still
# starting (common when sessions contend for CPU/disk under parallel load). A
# fresh attempt with a warm OS cache normally connects, so retry a bounded
# number of times before giving up. Terminal failures ("failed") are not retried.
MCP_UNAVAILABLE_MAX_RETRIES = 2  # extra attempts after the first (3 total)
MCP_UNAVAILABLE_RETRY_WAIT_SECONDS = 5.0

# Built-in tools override: empty string disables all built-in tools
# Forces Claude to use only MCP-provided tools
CLAUDE_BUILTIN_TOOLS = ""


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


class ParsedCliResponse(TypedDict):
    """Parsed CLI JSON response structure."""

    text: str
    session_id: str | None
    raw_response: dict[str, Any]


# MCP server status (from the init event) that means the server is ready to use.
_MCP_SERVER_READY_STATUS = "connected"

# Statuses worth retrying: a server still cold-starting ("pending") usually
# connects on a fresh attempt with a warm cache. Anything else (e.g. "failed",
# "unknown") is treated as terminal — a retry won't fix it.
_MCP_RETRYABLE_STATUSES = frozenset({"pending"})


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


def parse_cli_json_string(json_str: str) -> ParsedCliResponse:
    """Parse CLI JSON and extract fields (pure function).

    Extracts text and session_id from CLI JSON output.
    Uses verified field names from real CLI testing.

    Args:
        json_str: JSON string from CLI --output-format json

    Returns:
        dict with keys:
        - 'text' (str): Extracted response text from 'result' field
        - 'session_id' (str | None): Session ID if present, None otherwise
        - 'raw_response' (dict): Complete parsed JSON response

    Raises:
        ValueError: If JSON cannot be parsed

    Example:
        >>> json_str = '{"result": "Hello", "session_id": "abc"}'
        >>> data = parse_cli_json_string(json_str)
        >>> assert data["text"] == "Hello"
    """
    try:
        raw_response = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse CLI JSON: {e}") from e

    # Extract text from "result" field (verified from real CLI output)
    text = str(raw_response.get("result", ""))

    # Extract session_id with type validation
    session_id_raw = raw_response.get("session_id")
    if session_id_raw is not None:
        if not isinstance(session_id_raw, str):
            raise ValueError(
                f"session_id must be string, got {type(session_id_raw).__name__}"
            )
        session_id = session_id_raw
    else:
        session_id = None

    return ParsedCliResponse(
        text=text, session_id=session_id, raw_response=raw_response
    )


def format_stream_json_input(prompt: str) -> str:
    """Format a prompt as stream-json input for Claude CLI.

    When using --input-format stream-json, the prompt must be formatted as a
    JSON object with type "user" and a message containing the content.

    Args:
        prompt: The user's prompt text

    Returns:
        JSON-formatted string ready for stdin input

    Example:
        >>> result = format_stream_json_input("What is 2+2?")
        >>> import json
        >>> parsed = json.loads(result)
        >>> assert parsed["type"] == "user"
        >>> assert parsed["message"]["content"] == "What is 2+2?"
    """
    input_obj = {
        "type": "user",
        "message": {
            "role": "user",
            "content": prompt,
        },
    }
    return json.dumps(input_obj)


def build_cli_command(
    session_id: str | None,
    claude_cmd: str,
    mcp_config: str | None = None,
    use_stream_json: bool = True,
    append_system_prompt: str | None = None,
    system_prompt_replace: str | None = None,
    settings_file: str | None = None,
) -> list[str]:
    """Build CLI command arguments for stdin input (pure function).

    Uses stdin for prompt input to avoid Windows command-line length limits (~8191 chars).
    The prompt is passed via stdin using the -p "" pattern.

    If session_id is provided, uses --resume flag to continue Claude's native session.
    If mcp_config is provided, uses --mcp-config and --strict-mcp-config flags.
    If settings_file is provided, uses --settings flag to override cwd-discovered settings.

    When use_stream_json is True, enables complete conversation logging:
    - --output-format stream-json: NDJSON output with all messages
    - --input-format stream-json: Accepts JSON-formatted input
    - --replay-user-messages: Echoes user messages to stdout for complete logs
    - --verbose: Required for stream-json with -p mode

    Args:
        session_id: Optional Claude session ID to resume previous conversation
        claude_cmd: Path to claude executable
        mcp_config: Optional path to MCP config file
        use_stream_json: If True, use stream-json format for realtime output
            with complete logging including user prompts and tool interactions
        append_system_prompt: Optional system prompt to append via --append-system-prompt.
            Mutually exclusive with system_prompt_replace.
        system_prompt_replace: Optional system prompt to replace via --system-prompt.
            Mutually exclusive with append_system_prompt.
        settings_file: Optional path to Claude settings file passed via --settings,
            overriding matching keys in lower-precedence settings files for the session.

    Returns:
        Command list ready for subprocess execution with stdin

    Raises:
        ValueError: If required parameters are missing or invalid, or if both
            append_system_prompt and system_prompt_replace are provided.

    Example:
        >>> cmd = build_cli_command(None, "claude")
        >>> assert "--output-format" in cmd
        >>> assert "stream-json" in cmd
        >>> assert "--input-format" in cmd
        >>> assert "--replay-user-messages" in cmd

        >>> cmd = build_cli_command("abc123", "claude")
        >>> assert "--resume" in cmd and "abc123" in cmd

        >>> cmd = build_cli_command(None, "claude", ".mcp.json")
        >>> assert "--mcp-config" in cmd and ".mcp.json" in cmd

        >>> cmd = build_cli_command(
        ...     None, "claude", settings_file=".claude/settings.local.json"
        ... )
        >>> assert "--settings" in cmd and ".claude/settings.local.json" in cmd

        >>> cmd = build_cli_command(None, "claude", use_stream_json=False)
        >>> assert "json" in cmd and "stream-json" not in cmd
    """
    # Input validation
    if not claude_cmd or not claude_cmd.strip():
        raise ValueError("claude_cmd cannot be empty")
    if session_id is not None and not session_id.strip():
        raise ValueError("session_id cannot be empty string")

    # Use -p "" to read prompt from stdin (avoids command-line length limits)
    output_format = "stream-json" if use_stream_json else "json"
    command = [claude_cmd, "-p", "", "--output-format", output_format]

    # Disable all built-in tools, forcing use of MCP-provided tools only
    command.extend(["--tools", CLAUDE_BUILTIN_TOOLS])

    # stream-json output requires additional flags for complete logging
    if use_stream_json:
        # --verbose: Required for stream-json with -p (print mode)
        command.append("--verbose")
        # --input-format stream-json: Accept JSON-formatted input
        command.extend(["--input-format", "stream-json"])
        # --replay-user-messages: Echo user messages to stdout for complete logs
        # This ensures the user prompt is included in the NDJSON output
        command.append("--replay-user-messages")

    # Resume Claude's native session if session_id provided
    if session_id:
        command.extend(["--resume", session_id])

    # Add MCP config flags if mcp_config provided
    # --strict-mcp-config ensures Claude only uses servers from the specified config,
    # preventing fallback to default MCP configurations
    if mcp_config:
        command.extend(["--mcp-config", mcp_config, "--strict-mcp-config"])

    # Add Claude settings file if provided
    # --settings overrides matching keys in lower-precedence settings files
    # (project / user / managed) for the session.
    if settings_file:
        command.extend(["--settings", settings_file])

    # System prompt flags (mutually exclusive)
    if append_system_prompt and system_prompt_replace:
        raise ValueError(
            "Cannot specify both append_system_prompt and system_prompt_replace"
        )
    if append_system_prompt:
        command.extend(["--append-system-prompt", append_system_prompt])
    if system_prompt_replace:
        command.extend(["--system-prompt", system_prompt_replace])

    return command


def create_response_dict(
    text: str, session_id: str | None, raw_response: dict[str, Any]
) -> LLMResponseDict:
    """Create LLMResponseDict from parsed data (pure function).

    Args:
        text: Extracted response text
        session_id: Session ID (can be None)
        raw_response: Complete CLI JSON response

    Returns:
        Complete LLMResponseDict

    Example:
        >>> result = create_response_dict("Hello", "abc", {"result": "Hello"})
        >>> assert result["text"] == "Hello"
        >>> assert result["provider"] == "claude"
    """
    return {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "session_id": session_id,
        "provider": "claude",
        "raw_response": raw_response,
    }


def create_response_dict_from_stream(
    parsed: ParsedStreamResponse,
    stream_file: str | None = None,
) -> LLMResponseDict:
    """Create LLMResponseDict from parsed stream response.

    Args:
        parsed: Parsed stream response
        stream_file: Path to the stream log file (for reference)

    Returns:
        Complete LLMResponseDict
    """
    # Build raw_response from stream data
    raw_response: dict[str, Any] = {
        "messages": parsed["messages"],
        "stream_file": stream_file,
    }

    # Add result info if available
    if parsed["result_message"]:
        result_msg = parsed["result_message"]
        raw_response["result"] = result_msg.get("result", "")
        raw_response["is_error"] = result_msg.get("is_error", False)
        raw_response["duration_ms"] = result_msg.get("duration_ms")
        raw_response["total_cost_usd"] = result_msg.get("total_cost_usd")
        raw_response["usage"] = result_msg.get("usage")

    # Add system info if available
    if parsed["system_message"]:
        raw_response["system"] = parsed["system_message"]

    return {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": parsed["text"],
        "session_id": parsed["session_id"],
        "provider": "claude",
        "raw_response": raw_response,
    }


def _find_claude_executable() -> str:
    """Find Claude Code CLI executable, checking both PATH and common install locations.

    This is a wrapper around the shared find_claude_executable function,
    configured for CLI usage (tests execution and raises on not found).

    Returns:
        Path to Claude executable

    Raises:
        FileNotFoundError: If Claude Code CLI is not found
    """
    result = find_claude_executable(
        test_execution=True, return_none_if_not_found=False, fast_mode=True
    )
    if result is None:
        raise FileNotFoundError("Claude Code CLI not found")
    return result


def ask_claude_code_cli(
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
) -> LLMResponseDict:
    """Ask Claude via CLI with native session support and stream logging.

    Uses Claude CLI's native --resume flag for session continuity.
    Session management is handled by Claude Code CLI - no manual history needed.

    All CLI interactions are logged to NDJSON files in the logs directory for
    debugging and progress monitoring. The stream log file is continuously
    updated during execution, allowing real-time monitoring via `tail -f`.

    Args:
        question: The question to ask Claude
        session_id: Optional Claude session ID to resume previous conversation
        timeout: Timeout in seconds (default: 30)
        env_vars: Optional environment variables for the subprocess
        cwd: Optional working directory for the Claude subprocess.
            This controls where Claude executes, which affects:
            - Where .mcp.json config files are discovered
            - Resolution of relative file paths in prompts
            - Where Claude looks for local context files
            Note: This is separate from project_dir (which sets MCP_CODER_PROJECT_DIR).
            Default: None (subprocess uses caller's current working directory)
        mcp_config: Optional path to MCP config file
        settings_file: Optional path to Claude Code settings file (.claude/settings.local.json).
            When provided, passed to Claude via --settings, overriding matching keys
            in cwd-discovered settings for the session. None means Claude uses its
            cwd-based discovery as today.
        logs_dir: Optional logs directory for stream files (default: logs/claude-sessions)
        branch_name: Optional git branch name to include in log filename for context
        append_system_prompt: Optional system prompt to append via --append-system-prompt.
            Mutually exclusive with system_prompt_replace.
        system_prompt_replace: Optional system prompt to replace via --system-prompt.
            Mutually exclusive with append_system_prompt.

    Returns:
        LLMResponseDict with complete response data including session_id.
        The raw_response includes:
        - messages: List of all stream messages
        - stream_file: Path to the NDJSON log file
        - result: Final result text
        - duration_ms: Execution duration
        - total_cost_usd: API cost
        - usage: Token usage statistics

    Raises:
        ValueError: If input validation fails or JSON parsing fails
        TimeoutExpired: If command times out
        CalledProcessError: If command fails (includes stream_file path)
        McpServersUnavailableError: If a configured MCP server did not connect

    Examples:
        >>> # Start new conversation - get session_id from Claude
        >>> result = ask_claude_code_cli("Remember: my name is Alice")
        >>> session_id = result["session_id"]

        >>> # Resume conversation with Claude's session_id
        >>> result2 = ask_claude_code_cli("What's my name?", session_id=session_id)

        >>> # Monitor progress in real-time
        >>> # tail -f logs/claude-sessions/session_*.ndjson
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find executable
    claude_cmd = _find_claude_executable()

    # Build command with stream-json output format
    command = build_cli_command(
        session_id,
        claude_cmd,
        mcp_config,
        use_stream_json=True,
        append_system_prompt=append_system_prompt,
        system_prompt_replace=system_prompt_replace,
        settings_file=settings_file,
    )

    # Generate stream log file path
    stream_file_path = get_stream_log_path(logs_dir, cwd, branch_name)
    logger.debug(f"Stream log file: {stream_file_path}")

    # Log request
    log_llm_request(
        provider="claude",
        session_id=session_id,
        prompt=question,
        timeout=timeout,
        env_vars=env_vars or {},
        cwd=cwd or "",
        command=command,
        mcp_config=mcp_config,
    )

    # Execute command with stdin input (I/O)
    # cwd parameter controls where Claude subprocess runs
    # This affects .mcp.json discovery and relative path resolution
    #
    # When using stream-json input format, the prompt must be formatted as JSON
    # to enable --replay-user-messages which echoes the prompt in the output
    input_data = format_stream_json_input(question)
    logger.debug(
        f"Executing CLI command with stdin (prompt_len={len(question)}, "
        f"input_format=stream-json, session_id={session_id}, cwd={cwd})"
    )
    options = CommandOptions(
        timeout_seconds=timeout,
        input_data=input_data,  # Pass JSON-formatted question via stdin
        env=env_vars,
        cwd=cwd,  # Set working directory for Claude subprocess execution
        env_remove=["CLAUDECODE"],  # Allow nested Claude CLI invocations
    )

    parsed: ParsedStreamResponse | None = None
    stream_file_str = str(stream_file_path)

    try:
        attempt = 0
        while True:
            attempt += 1
            start_time = time.time()
            result = execute_subprocess(
                command,
                options,
                heartbeat_interval_seconds=LLM_HEARTBEAT_INTERVAL_SECONDS,
                heartbeat_message="LLM call in progress",
            )

            # Save stream output to file
            if result.stdout:
                try:
                    stream_file_path.write_text(result.stdout, encoding="utf-8")
                    logger.debug(
                        f"Wrote {len(result.stdout)} bytes to {stream_file_path}"
                    )
                except (OSError, IOError) as e:
                    logger.warning(f"Failed to write stream file: {e}")

            # Parse stream output
            parsed = parse_stream_json_string(result.stdout)

            # Error handling
            if result.timed_out:
                logger.error(f"CLI timed out after {timeout}s")
                duration_ms = int((time.time() - start_time) * 1000)
                timeout_error: Exception = TimeoutExpired(command, timeout)
                log_llm_error(error=timeout_error, duration_ms=duration_ms)
                raise timeout_error

            if result.return_code != 0:
                logger.error(f"CLI failed with code {result.return_code}")
                logger.error(f"Stream file for diagnosis: {stream_file_path}")
                duration_ms = int((time.time() - start_time) * 1000)

                # Include stream file path in error for diagnosis
                error_msg = (
                    f"CLI failed with code {result.return_code}. "
                    f"Stream log: {stream_file_path}"
                )
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr[:500]}"

                called_process_error = CalledProcessError(
                    result.return_code,
                    command,
                    output=result.stdout,
                    stderr=f"{result.stderr}\nStream file: {stream_file_path}",
                )
                log_llm_error(error=called_process_error, duration_ms=duration_ms)
                raise called_process_error

            # MCP availability guard. A "pending" server is usually still
            # cold-starting; retry a bounded number of times (a warm cache
            # normally connects) before aborting so the model never runs blind.
            unavailable_servers = find_unavailable_mcp_servers(parsed["system_message"])
            if unavailable_servers:
                detail = ", ".join(
                    f"{name}={status}" for name, status in unavailable_servers
                )
                mcp_error_msg = (
                    f"MCP servers not available: {detail}. The session started "
                    f"without its configured tools. Stream log: {stream_file_path}"
                )
                if (
                    mcp_failure_is_retryable(unavailable_servers)
                    and attempt <= MCP_UNAVAILABLE_MAX_RETRIES
                ):
                    logger.warning(
                        "%s Retrying (attempt %d/%d) after %.0fs.",
                        mcp_error_msg,
                        attempt + 1,
                        MCP_UNAVAILABLE_MAX_RETRIES + 1,
                        MCP_UNAVAILABLE_RETRY_WAIT_SECONDS,
                    )
                    time.sleep(MCP_UNAVAILABLE_RETRY_WAIT_SECONDS)
                    continue
                logger.error(mcp_error_msg)
                duration_ms = int((time.time() - start_time) * 1000)
                mcp_error: Exception = McpServersUnavailableError(
                    mcp_error_msg, unavailable_servers=unavailable_servers
                )
                log_llm_error(error=mcp_error, duration_ms=duration_ms)
                raise mcp_error

            # Success — leave the retry loop.
            break

        logger.debug(
            f"CLI success: {len(result.stdout)} bytes, session_id={parsed['session_id']}"
        )

        # Log response
        duration_ms = int((time.time() - start_time) * 1000)

        # Extract cost info from result message
        cost_usd = None
        usage = None
        if parsed["result_message"]:
            cost_usd = parsed["result_message"].get("total_cost_usd")
            usage = parsed["result_message"].get("usage")

        log_llm_response(
            duration_ms=duration_ms,
            session_id=parsed["session_id"],
            cost_usd=cost_usd,
            usage=usage,
        )

        # Create response dict from stream data
        return create_response_dict_from_stream(parsed, stream_file_str)

    except (TimeoutExpired, CalledProcessError, McpServersUnavailableError):
        # Already logged above - re-raise without logging again
        raise
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        # Log any other unexpected errors (e.g., ValueError from JSON parsing)
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(error=e, duration_ms=duration_ms)

        # Try to save whatever output we have
        if parsed is None:
            logger.error(f"Stream file for diagnosis: {stream_file_path}")

        raise
