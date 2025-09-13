#!/usr/bin/env python3
"""Claude Code client for programmatic interaction."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _find_claude_executable() -> str:
    """Find Claude Code CLI executable, checking both PATH and common install locations."""
    # First, try to find claude in PATH
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return "claude"  # Available in PATH
    except (FileNotFoundError, subprocess.TimeoutExpired):
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
                result = subprocess.run(
                    [str(claude_path), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5,  # Reduced timeout
                    check=False,
                )
                # If it doesn't crash immediately, assume it's working
                if result.returncode in [0, 1]:  # 0 = success, 1 = help shown
                    return str(claude_path)
            except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
                # If it exists as a file, return it anyway - might work for actual commands
                return str(claude_path)

    raise FileNotFoundError(
        "Claude Code CLI not found. Please ensure it's installed and accessible."
    )


def ask_claude(question: str, timeout: int = 30) -> str:
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
        result = subprocess.run(
            [claude_cmd, "--print", question],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )

        return result.stdout.strip()

    except FileNotFoundError:
        # This will be raised by _find_claude_executable if not found
        raise
    except subprocess.TimeoutExpired as e:
        raise subprocess.TimeoutExpired(
            e.cmd, e.timeout, f"Claude Code command timed out after {timeout} seconds"
        )
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode,
            e.cmd,
            output=e.output,
            stderr=f"Claude Code command failed: {e.stderr}",
        )


