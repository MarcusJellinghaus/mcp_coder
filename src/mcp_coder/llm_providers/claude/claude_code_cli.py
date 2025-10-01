#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import logging
import subprocess
import tempfile
from pathlib import Path

from ...utils.subprocess_runner import (
    CommandOptions,
    execute_command,
    execute_subprocess,
)
from .claude_executable_finder import find_claude_executable

logger = logging.getLogger(__name__)


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
    question: str, timeout: int = 30, cwd: str | None = None
) -> str:
    """
    Ask Claude a question via Claude Code CLI and return the response.

    Uses stdin input for long prompts to avoid Windows command line length limits.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the command (default: 30)
        cwd: Working directory for the command (default: None, uses current directory)
             This is important for Claude to find .claude/settings.local.json

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

    # Windows command line limit is ~8191 characters
    # Use stdin for long prompts to avoid this limitation
    command_line_length = len(claude_cmd) + len("--print ") + len(question)

    if command_line_length > 7000:  # Conservative threshold
        # Use stdin input method: echo "prompt" | claude -p ""
        logger.debug(f"Executing: {claude_cmd} -p '' (with stdin input, cwd={cwd})")
        options = CommandOptions(timeout_seconds=timeout, input_data=question, cwd=cwd)
        result = execute_subprocess([claude_cmd, "-p", ""], options)
    else:
        # Use direct command line argument for shorter prompts
        logger.debug(f"Executing: {claude_cmd} --print <question> (cwd={cwd})")
        result = execute_command(
            [claude_cmd, "--print", question],
            timeout_seconds=timeout,
            cwd=cwd,
        )

    if result.timed_out:
        logger.error(f"Claude Code CLI timed out after {timeout} seconds")
        raise subprocess.TimeoutExpired(
            result.command or [claude_cmd],
            timeout,
            f"Claude Code command timed out after {timeout} seconds",
        )

    if result.return_code != 0:
        logger.error(f"Claude Code CLI failed with return code {result.return_code}")
        raise subprocess.CalledProcessError(
            result.return_code,
            result.command or [claude_cmd],
            output=result.stdout,
            stderr=f"Claude Code command failed: {result.stderr}",
        )

    logger.debug(f"Claude CLI success: response length={len(result.stdout.strip())}")

    return result.stdout.strip()
