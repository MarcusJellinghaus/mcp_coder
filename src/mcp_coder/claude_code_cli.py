#!/usr/bin/env python3
"""Claude Code CLI implementation for programmatic interaction."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .subprocess_runner import execute_command


def _find_claude_executable() -> str:
    """Find Claude Code CLI executable, checking both PATH and common install locations."""
    # First, try to find claude in PATH
    try:
        result = execute_command(
            ["claude", "--version"],
            timeout_seconds=10,
        )
        if result.return_code == 0:
            return "claude"  # Available in PATH
    except Exception:
        pass

    # Try common installation locations
    username = os.environ.get("USERNAME", os.environ.get("USER", ""))
    possible_locations = [
        f"C:\\Users\\{username}\\.local\\bin\\claude.exe",
        f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Claude\\claude.exe",
        f"C:\\Users\\{username}\\AppData\\Roaming\\Claude\\claude.exe",
        "/usr/local/bin/claude",
        "/opt/claude/claude",
        f"{os.path.expanduser('~')}/.local/bin/claude",
    ]

    for location in possible_locations:
        claude_path = Path(location)
        if claude_path.exists() and claude_path.is_file():
            try:
                # Test if the executable works with a simple help command (faster than --version)
                result = execute_command(
                    [str(claude_path), "--help"],
                    timeout_seconds=5,
                )
                # If it doesn't crash immediately, assume it's working
                if result.return_code in [0, 1]:  # 0 = success, 1 = help shown
                    return str(claude_path)
            except Exception:
                # If it exists as a file, return it anyway - might work for actual commands
                return str(claude_path)

    raise FileNotFoundError(
        "Claude Code CLI not found. Please ensure it's installed and accessible."
    )


def ask_claude_code_cli(question: str, timeout: int = 30) -> str:
    """
    Ask Claude a question via Claude Code CLI and return the response.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the command (default: 30)

    Returns:
        Claude's response as a string

    Raises:
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If the command fails
        FileNotFoundError: If Claude Code CLI is not found
    """
    try:
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

    except FileNotFoundError:
        # This will be raised by _find_claude_executable if not found
        raise
    except subprocess.TimeoutExpired:
        # Re-raise timeout errors
        raise
    except subprocess.CalledProcessError:
        # Re-raise command errors
        raise
