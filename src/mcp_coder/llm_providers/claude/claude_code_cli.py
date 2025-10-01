#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

from ...llm_types import LLM_RESPONSE_VERSION, LLMResponseDict
from ...utils.subprocess_runner import (
    CommandOptions,
    execute_command,
    execute_subprocess,
)
from .claude_executable_finder import find_claude_executable

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

    # Extract session_id
    session_id_raw = raw_response.get("session_id")
    session_id = str(session_id_raw) if session_id_raw is not None else None

    return ParsedCliResponse(
        text=text, session_id=session_id, raw_response=raw_response
    )


def build_cli_command(
    question: str, session_id: str | None, claude_cmd: str
) -> list[str]:
    """Build CLI command arguments (pure function).

    Args:
        question: Question to ask
        session_id: Optional session ID for continuation
        claude_cmd: Path to claude executable

    Returns:
        Command list ready for subprocess execution

    Example:
        >>> cmd = build_cli_command("test", None, "claude")
        >>> assert cmd == ["claude", "--print", "--output-format", "json", "test"]
    """
    command = [claude_cmd, "--print", "--output-format", "json"]

    if session_id:
        command.extend(["--resume", session_id])

    command.append(question)
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
        test_execution=True, return_none_if_not_found=False, fast_mode=False
    )
    if result is None:
        raise FileNotFoundError("Claude Code CLI not found")
    return result


def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:
    """Ask Claude via CLI and return structured response (I/O wrapper).

    Thin wrapper that handles subprocess execution, delegating parsing
    and response construction to pure functions.

    Args:
        question: The question to ask Claude
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds (default: 30)
        cwd: Working directory (default: None)

    Returns:
        LLMResponseDict with complete response data

    Raises:
        ValueError: If input validation fails or JSON parsing fails
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails

    Examples:
        >>> # Start new conversation
        >>> result = ask_claude_code_cli("What is Python?")
        >>> print(result["text"])
        >>> session_id = result["session_id"]

        >>> # Continue conversation
        >>> result2 = ask_claude_code_cli("Tell me more", session_id=session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find executable
    claude_cmd = _find_claude_executable()

    # Build command (pure function)
    command = build_cli_command(question, session_id, claude_cmd)

    # Execute command (I/O)
    logger.debug(f"Executing CLI command (cwd={cwd})")
    result = execute_command(command, timeout_seconds=timeout, cwd=cwd)

    # Error handling
    if result.timed_out:
        logger.error(f"CLI timed out after {timeout}s")
        raise subprocess.TimeoutExpired(command, timeout)

    if result.return_code != 0:
        logger.error(f"CLI failed with code {result.return_code}")
        raise subprocess.CalledProcessError(
            result.return_code, command, output=result.stdout, stderr=result.stderr
        )

    logger.debug(f"CLI success: {len(result.stdout)} bytes")

    # Parse JSON (pure function)
    parsed = parse_cli_json_string(result.stdout.strip())

    # Create response dict (pure function)
    return create_response_dict(
        parsed["text"], parsed["session_id"], parsed["raw_response"]
    )
