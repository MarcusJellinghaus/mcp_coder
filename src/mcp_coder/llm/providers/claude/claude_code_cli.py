#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import json
import logging
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

from ....utils.subprocess_runner import (
    CommandOptions,
    execute_command,
    execute_subprocess,
)
from ...types import LLM_RESPONSE_VERSION, LLMResponseDict
from .claude_executable_finder import find_claude_executable
from .logging_utils import log_llm_error, log_llm_request, log_llm_response

logger = logging.getLogger(__name__)


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


def build_cli_command(
    session_id: str | None, claude_cmd: str, mcp_config: str | None = None
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

    Returns:
        Command list ready for subprocess execution with stdin

    Example:
        >>> cmd = build_cli_command(None, "claude")
        >>> assert cmd == ["claude", "-p", "", "--output-format", "json"]

        >>> cmd = build_cli_command("abc123", "claude")
        >>> assert "--resume" in cmd and "abc123" in cmd

        >>> cmd = build_cli_command(None, "claude", ".mcp.json")
        >>> assert "--mcp-config" in cmd and ".mcp.json" in cmd
    """
    # Input validation
    if not claude_cmd or not claude_cmd.strip():
        raise ValueError("claude_cmd cannot be empty")
    if session_id is not None and not session_id.strip():
        raise ValueError("session_id cannot be empty string")

    # Use -p "" to read prompt from stdin (avoids command-line length limits)
    command = [claude_cmd, "-p", "", "--output-format", "json"]

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
) -> LLMResponseDict:
    """Ask Claude via CLI with native session support.

    Uses Claude CLI's native --resume flag for session continuity.
    Session management is handled by Claude Code CLI - no manual history needed.

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

    Returns:
        LLMResponseDict with complete response data including session_id

    Raises:
        ValueError: If input validation fails or JSON parsing fails
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails

    Examples:
        >>> # Start new conversation - get session_id from Claude
        >>> result = ask_claude_code_cli("Remember: my name is Alice")
        >>> session_id = result["session_id"]

        >>> # Resume conversation with Claude's session_id
        >>> result2 = ask_claude_code_cli("What's my name?", session_id=session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find executable
    claude_cmd = _find_claude_executable()

    # Build command with optional --resume and --mcp-config (pure function)
    command = build_cli_command(session_id, claude_cmd, mcp_config)

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

    try:
        result = execute_subprocess(command, options)

        # Error handling
        if result.timed_out:
            logger.error(f"CLI timed out after {timeout}s")
            duration_ms = int((time.time() - start_time) * 1000)
            timeout_error: Exception = subprocess.TimeoutExpired(command, timeout)
            log_llm_error(method="cli", error=timeout_error, duration_ms=duration_ms)
            raise timeout_error

        if result.return_code != 0:
            logger.error(f"CLI failed with code {result.return_code}")
            duration_ms = int((time.time() - start_time) * 1000)
            called_process_error: Exception = subprocess.CalledProcessError(
                result.return_code, command, output=result.stdout, stderr=result.stderr
            )
            log_llm_error(
                method="cli", error=called_process_error, duration_ms=duration_ms
            )
            raise called_process_error

        logger.debug(
            f"CLI success: {len(result.stdout)} bytes, session_id from response"
        )

        # Log response
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_response(method="cli", duration_ms=duration_ms)

        # Parse JSON (pure function)
        parsed = parse_cli_json_string(result.stdout.strip())

        # Create response dict (pure function)
        return create_response_dict(
            parsed["text"], parsed["session_id"], parsed["raw_response"]
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
        # These errors are already logged above
        raise
    except Exception as e:
        # Log any other unexpected errors
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(method="cli", error=e, duration_ms=duration_ms)
        raise
