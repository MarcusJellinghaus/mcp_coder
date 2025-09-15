#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import subprocess

from .claude_executable_finder import find_claude_executable
from ...utils.subprocess_runner import execute_command


def _find_claude_executable() -> str:
    """Find Claude Code CLI executable, checking both PATH and common install locations.

    This is a wrapper around the shared find_claude_executable function,
    configured for CLI usage (tests execution and raises on not found).

    Returns:
        Path to Claude executable

    Raises:
        FileNotFoundError: If Claude Code CLI is not found
    """
    result = find_claude_executable(test_execution=True, return_none_if_not_found=False)
    if result is None:
        raise FileNotFoundError("Claude Code CLI not found")
    return result


def ask_claude_code_cli(question: str, timeout: int = 30) -> str:
    """
    Ask Claude a question via Claude Code CLI and return the response.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the command (default: 30)

    Returns:
        Claude's response as a string

    Raises:
        ValueError: If input validation fails
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If the command fails
        FileNotFoundError: If Claude Code CLI is not found
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find the Claude executable
    claude_cmd = _find_claude_executable()

    # Use Claude Code CLI to ask the question
    result = execute_command(
        [claude_cmd, "--print", question],
        timeout_seconds=timeout,
    )

    if result.timed_out:
        raise subprocess.TimeoutExpired(
            [claude_cmd, "--print", question],
            timeout,
            f"Claude Code command timed out after {timeout} seconds",
        )

    if result.return_code != 0:
        raise subprocess.CalledProcessError(
            result.return_code,
            [claude_cmd, "--print", question],
            output=result.stdout,
            stderr=f"Claude Code command failed: {result.stderr}",
        )

    return result.stdout.strip()
