#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import json
import logging
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

from ....utils.subprocess_runner import (
    CommandOptions,
    execute_subprocess,
)
from ...types import LLM_RESPONSE_VERSION, LLMResponseDict
from .claude_executable_finder import find_claude_executable
from .logging_utils import log_llm_error, log_llm_request, log_llm_response

logger = logging.getLogger(__name__)

# Default logs directory for stream output
DEFAULT_LOGS_DIR = "logs"
CLAUDE_SESSIONS_SUBDIR = "claude-sessions"


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


class CLIError(Exception):
    """CLI error with stream messages for diagnosis."""

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        stream_messages: list[StreamMessage] | None = None,
        stream_file: str | None = None,
    ):
        super().__init__(message)
        self.original_error = original_error
        self.stream_messages = stream_messages or []
        self.stream_file = stream_file


def sanitize_branch_identifier(branch_name: str | None) -> str:
    """Sanitize a branch name into a short identifier for filenames.

    Extracts a meaningful short identifier from the branch name:
    - For branches like '123-feature-name', returns '123'
    - For branches like 'fix/improve-logging', returns 'fix'
    - Sanitizes special characters
    - Returns max 10 characters

    Args:
        branch_name: Full branch name (e.g., 'fix/improve-logging')

    Returns:
        Sanitized identifier (max 10 chars), or empty string if None/empty

    Example:
        >>> sanitize_branch_identifier('123-feature-name')
        '123'
        >>> sanitize_branch_identifier('fix/improve-logging')
        'fix'
        >>> sanitize_branch_identifier(None)
        ''
    """
    if not branch_name:
        return ""

    branch = branch_name.strip()
    if not branch or branch == "HEAD":
        return ""

    # Extract first meaningful part:
    # - Split on / (e.g., 'fix/improve-logging' -> 'fix')
    # - Split on - (e.g., '123-feature-name' -> '123')
    parts_slash = branch.split("/")
    parts_dash = branch.split("-")

    # Prefer numeric issue IDs if present at the start
    first_dash = parts_dash[0] if parts_dash else ""
    first_slash = parts_slash[0] if parts_slash else ""

    # If first dash part is numeric (issue ID), use it
    if first_dash and first_dash.isdigit():
        identifier = first_dash
    # Otherwise use the first slash part (e.g., 'fix', 'feat', 'feature')
    elif first_slash:
        identifier = first_slash
    else:
        identifier = branch

    # Sanitize: keep only alphanumeric and underscore
    identifier = re.sub(r"[^a-zA-Z0-9_]", "", identifier)

    # Limit to 10 characters
    return identifier[:10]


def get_stream_log_path(
    logs_dir: str | None = None,
    cwd: str | None = None,
    branch_name: str | None = None,
) -> Path:
    """Generate a unique path for stream log file.

    The filename includes:
    - Timestamp for uniqueness
    - Git branch identifier (max 10 chars) for context (if provided)

    Example filenames:
    - session_20260201_123456_789012_fix.ndjson (branch: fix/improve-logging)
    - session_20260201_123456_789012_123.ndjson (branch: 123-feature-name)
    - session_20260201_123456_789012.ndjson (no branch provided)

    Args:
        logs_dir: Base logs directory (default: 'logs' in cwd or project root)
        cwd: Working directory context
        branch_name: Optional git branch name to include in filename

    Returns:
        Path to the stream log file
    """
    # Determine base directory
    if logs_dir:
        base_dir = Path(logs_dir)
    elif cwd:
        base_dir = Path(cwd) / DEFAULT_LOGS_DIR
    else:
        base_dir = Path.cwd() / DEFAULT_LOGS_DIR

    # Create claude-sessions subdirectory
    session_dir = base_dir / CLAUDE_SESSIONS_SUBDIR
    session_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename with timestamp and optional branch identifier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    branch_id = sanitize_branch_identifier(branch_name)

    if branch_id:
        filename = f"session_{timestamp}_{branch_id}.ndjson"
    else:
        filename = f"session_{timestamp}.ndjson"

    return session_dir / filename


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


def parse_stream_json_file(file_path: Path) -> ParsedStreamResponse:
    """Parse a stream-json log file into structured response.

    Args:
        file_path: Path to the NDJSON stream log file

    Returns:
        ParsedStreamResponse with extracted text, session_id, and all messages
    """
    messages: list[StreamMessage] = []
    text_parts: list[str] = []
    session_id: str | None = None
    result_message: StreamMessage | None = None
    system_message: StreamMessage | None = None

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
        for line in content.splitlines():
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

    except (OSError, IOError) as e:
        logger.error(f"Failed to read stream file {file_path}: {e}")

    return ParsedStreamResponse(
        text="".join(text_parts).strip(),
        session_id=session_id,
        messages=messages,
        result_message=result_message,
        system_message=system_message,
    )


def parse_stream_json_string(content: str) -> ParsedStreamResponse:
    """Parse stream-json content from a string.

    Args:
        content: NDJSON content as a string

    Returns:
        ParsedStreamResponse with extracted data
    """
    messages: list[StreamMessage] = []
    text_parts: list[str] = []
    session_id: str | None = None
    result_message: StreamMessage | None = None
    system_message: StreamMessage | None = None

    for line in content.splitlines():
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


def build_cli_command(
    session_id: str | None,
    claude_cmd: str,
    mcp_config: str | None = None,
    use_stream_json: bool = True,
) -> list[str]:
    """Build CLI command arguments for stdin input (pure function).

    Uses stdin for prompt input to avoid Windows command-line length limits (~8191 chars).
    The prompt is passed via stdin using the -p "" pattern.

    If session_id is provided, uses --resume flag to continue Claude's native session.
    If mcp_config is provided, uses --mcp-config and --strict-mcp-config flags.

    Args:
        session_id: Optional Claude session ID to resume previous conversation
        claude_cmd: Path to claude executable
        mcp_config: Optional path to MCP config file
        use_stream_json: If True, use stream-json format for realtime output

    Returns:
        Command list ready for subprocess execution with stdin

    Example:
        >>> cmd = build_cli_command(None, "claude")
        >>> assert "--output-format" in cmd
        >>> assert "stream-json" in cmd

        >>> cmd = build_cli_command("abc123", "claude")
        >>> assert "--resume" in cmd and "abc123" in cmd

        >>> cmd = build_cli_command(None, "claude", ".mcp.json")
        >>> assert "--mcp-config" in cmd and ".mcp.json" in cmd

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

    # stream-json requires --verbose when using -p (print mode)
    if use_stream_json:
        command.append("--verbose")

    # Resume Claude's native session if session_id provided
    if session_id:
        command.extend(["--resume", session_id])

    # Add MCP config flags if mcp_config provided
    # --strict-mcp-config ensures Claude only uses servers from the specified config,
    # preventing fallback to default MCP configurations
    if mcp_config:
        command.extend(["--mcp-config", mcp_config, "--strict-mcp-config"])

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
        >>> assert result["method"] == "cli"
    """
    return {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "session_id": session_id,
        "method": "cli",
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
        "method": "cli",
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
    logs_dir: str | None = None,
    branch_name: str | None = None,
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
        logs_dir: Optional logs directory for stream files (default: logs/claude-sessions)
        branch_name: Optional git branch name to include in log filename for context

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
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails (includes stream_file path)

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
        session_id, claude_cmd, mcp_config, use_stream_json=True
    )

    # Generate stream log file path
    stream_file_path = get_stream_log_path(logs_dir, cwd, branch_name)
    logger.debug(f"Stream log file: {stream_file_path}")

    # Log request
    log_llm_request(
        method="cli",
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
    logger.debug(
        f"Executing CLI command with stdin (prompt_len={len(question)}, "
        f"session_id={session_id}, cwd={cwd})"
    )
    start_time = time.time()
    options = CommandOptions(
        timeout_seconds=timeout,
        input_data=question,  # Pass question via stdin
        env=env_vars,
        cwd=cwd,  # Set working directory for Claude subprocess execution
    )

    parsed: ParsedStreamResponse | None = None
    stream_file_str = str(stream_file_path)

    try:
        result = execute_subprocess(command, options)

        # Save stream output to file
        if result.stdout:
            try:
                stream_file_path.write_text(result.stdout, encoding="utf-8")
                logger.debug(f"Wrote {len(result.stdout)} bytes to {stream_file_path}")
            except (OSError, IOError) as e:
                logger.warning(f"Failed to write stream file: {e}")

        # Parse stream output
        parsed = parse_stream_json_string(result.stdout)

        # Error handling
        if result.timed_out:
            logger.error(f"CLI timed out after {timeout}s")
            duration_ms = int((time.time() - start_time) * 1000)
            timeout_error: Exception = subprocess.TimeoutExpired(command, timeout)
            log_llm_error(method="cli", error=timeout_error, duration_ms=duration_ms)
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

            called_process_error = subprocess.CalledProcessError(
                result.return_code,
                command,
                output=result.stdout,
                stderr=f"{result.stderr}\nStream file: {stream_file_path}",
            )
            log_llm_error(
                method="cli", error=called_process_error, duration_ms=duration_ms
            )
            raise called_process_error

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
            method="cli", duration_ms=duration_ms, cost_usd=cost_usd, usage=usage
        )

        # Create response dict from stream data
        return create_response_dict_from_stream(parsed, stream_file_str)

    except subprocess.TimeoutExpired:
        # Already logged above - re-raise without logging again
        raise
    except subprocess.CalledProcessError:
        # Already logged above - re-raise without logging again
        raise
    except Exception as e:
        # Log any other unexpected errors (e.g., ValueError from JSON parsing)
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(method="cli", error=e, duration_ms=duration_ms)

        # Try to save whatever output we have
        if parsed is None:
            logger.error(f"Stream file for diagnosis: {stream_file_path}")

        raise
