#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import json
import logging
import time
from datetime import datetime
from typing import Any, TypedDict

from ....utils.subprocess_runner import (
    CalledProcessError,
    TimeoutExpired,
)
from ...logging_utils import log_llm_error, log_llm_request, log_llm_response
from ...types import (
    LLM_RESPONSE_VERSION,
    LLMResponseDict,
    ResponseAssembler,
    StreamEvent,
)
from .claude_executable_finder import find_claude_executable

# Stream-json parsing and the MCP-availability guard live in claude_mcp_guard.
# They are re-exported here so existing importers (and patch targets) keep
# working from claude_code_cli unchanged.
from .claude_mcp_guard import (
    McpServersUnavailableError,
    ParsedStreamResponse,
    StreamMessage,
    find_exposed_mcp_tools,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
    parse_stream_json_file,
    parse_stream_json_line,
    parse_stream_json_string,
)

logger = logging.getLogger(__name__)

# Built-in tools override: keep "ToolSearch" as the MCP wait-bridge so the model
# can wait for a still-pending MCP server instead of running blind, while
# file/exec built-ins (Bash/Edit/Read/Write) stay disabled. MCP tools load
# independently via --mcp-config.
CLAUDE_BUILTIN_TOOLS = "ToolSearch"

__all__ = [
    "CLAUDE_BUILTIN_TOOLS",
    "McpServersUnavailableError",
    "ParsedCliResponse",
    "ParsedStreamResponse",
    "StreamMessage",
    "ask_claude_code_cli",
    "build_cli_command",
    "create_response_dict",
    "find_exposed_mcp_tools",
    "find_fatal_mcp_servers",
    "find_unavailable_mcp_servers",
    "format_stream_json_input",
    "parse_cli_json_string",
    "parse_stream_json_file",
    "parse_stream_json_line",
    "parse_stream_json_string",
]


class ParsedCliResponse(TypedDict):
    """Parsed CLI JSON response structure."""

    text: str
    session_id: str | None
    raw_response: dict[str, Any]


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

    # Keep only ToolSearch (the MCP wait-bridge); all other built-ins
    # (Bash/Edit/Read/Write) stay disabled.
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

    This is a thin drain-wrapper over :func:`ask_claude_code_cli_stream`: it
    consumes the streaming generator to completion, assembles the result via
    :class:`ResponseAssembler`, translates the streaming error events back into
    exceptions, and runs the ``log_llm_*`` side-effects. The ``timeout`` is an
    *inactivity* budget (max seconds with no stdout line from ``claude``), not a
    wall-clock cap, since the streaming core watches for inactivity.

    Returns:
        LLMResponseDict with complete response data including session_id.
        The raw_response is the assembler's ``events`` shape:
        - events: List of every StreamEvent seen during the run
        - stream_file: Path to the NDJSON log file
        - usage: Token usage statistics (when present)

    Raises:
        ValueError: If input validation fails
        TimeoutExpired: On inactivity timeout (reason ``inactivity_timeout``)
        CalledProcessError: If the CLI exits non-zero (includes stream_file path)
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

    # Lazy (function-local) import to avoid the claude_code_cli <->
    # claude_code_cli_streaming circular import: the streaming module imports
    # helpers from this module at load time.
    from .claude_code_cli_streaming import (  # pylint: disable=cyclic-import
        ask_claude_code_cli_stream,
    )

    # The real argv is built inside ask_claude_code_cli_stream and is not
    # exposed here; log a stable placeholder. The stream file path (captured
    # below) is what actually identifies the run.
    cmd_label = ["claude", "-p"]
    log_llm_request(
        provider="claude",
        session_id=session_id,
        prompt=question,
        timeout=timeout,
        env_vars=env_vars or {},
        cwd=cwd or "",
        command=cmd_label,
        mcp_config=mcp_config,
    )

    start_time = time.time()
    assembler = ResponseAssembler("claude")
    last_error: StreamEvent | None = None
    done: StreamEvent | None = None
    stream_file: str | None = None

    # Drain the streaming core to completion. McpServersUnavailableError is
    # raised mid-iteration by the generator and is allowed to propagate.
    try:
        for event in ask_claude_code_cli_stream(
            question,
            session_id=session_id,
            timeout=timeout,
            env_vars=env_vars,
            cwd=cwd,
            mcp_config=mcp_config,
            settings_file=settings_file,
            logs_dir=logs_dir,
            branch_name=branch_name,
            append_system_prompt=append_system_prompt,
            system_prompt_replace=system_prompt_replace,
        ):
            assembler.add(event)
            event_type = event.get("type")
            if event_type == "stream_file":
                path = event.get("path")
                if isinstance(path, str):
                    stream_file = path
            elif event_type == "done":
                done = event
            elif event_type == "error":
                last_error = event
    except McpServersUnavailableError as mcp_error:
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(error=mcp_error, duration_ms=duration_ms)
        raise

    duration_ms = int((time.time() - start_time) * 1000)

    # Inactivity timeout: distinguished from a generic failure by the structured
    # `reason` discriminator on the error event. Re-raise TimeoutExpired so the
    # existing interface.py -> LLMTimeoutError bridge still applies.
    if last_error is not None and last_error.get("reason") == "inactivity_timeout":
        timeout_error: Exception = TimeoutExpired(cmd_label, timeout)
        log_llm_error(error=timeout_error, duration_ms=duration_ms)
        raise timeout_error

    # Any other error event is a non-zero CLI exit.
    if last_error is not None:
        rc = last_error.get("return_code")
        return_code = rc if isinstance(rc, int) else 1
        # Preserve the streaming error event's message (carries stderr[:500] and
        # detail) so log_llm_error and callers keep the diagnostic context.
        error_message = last_error.get("message")
        stderr_detail = (
            f"CLI failed with code {return_code}. Stream file: {stream_file}"
        )
        if isinstance(error_message, str) and error_message:
            stderr_detail = f"{error_message} Stream file: {stream_file}"
        called_process_error = CalledProcessError(
            return_code,
            cmd_label,
            output="",
            stderr=stderr_detail,
        )
        log_llm_error(error=called_process_error, duration_ms=duration_ms)
        raise called_process_error

    result = assembler.result()

    # Extract cost/usage from the done event for the response log.
    cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    if done is not None:
        cost_value = done.get("cost_usd")
        if isinstance(cost_value, (int, float)) and not isinstance(cost_value, bool):
            cost_usd = float(cost_value)
        usage_value = done.get("usage")
        if isinstance(usage_value, dict):
            usage = usage_value

    log_llm_response(
        duration_ms=duration_ms,
        session_id=result["session_id"],
        cost_usd=cost_usd,
        usage=usage,
    )
    return result
