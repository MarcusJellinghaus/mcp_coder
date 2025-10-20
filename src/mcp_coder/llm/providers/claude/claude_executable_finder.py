#!/usr/bin/env python3
"""Shared utilities for finding and managing Claude Code executable."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Optional

from ....utils.subprocess_runner import execute_command


def _get_claude_search_paths() -> List[str]:
    """Get list of common Claude installation paths to search.

    Returns:
        List of potential Claude executable paths
    """
    paths_list: List[str] = []
    
    # First check PATH (highest priority)
    claude_from_path = shutil.which("claude")
    if claude_from_path is not None:
        paths_list.append(claude_from_path)

    # Native installer locations - highest priority after PATH
    # These are the standard locations for the native Claude Code installer
    # Use os.path.join for proper path construction across platforms
    user_home = os.path.expanduser("~")
    paths_list.extend([
        os.path.join(user_home, ".local", "bin", "claude.exe"),
        os.path.join(user_home, ".local", "bin", "claude"),
    ])

    # Node.js global install locations
    paths_list.extend([
        os.path.join(user_home, "node_modules", ".bin", "claude.exe"),
        os.path.join(user_home, "node_modules", ".bin", "claude"),
        os.path.join(user_home, "AppData", "Roaming", "npm", "claude.exe"),
        os.path.join(user_home, "AppData", "Roaming", "npm", "claude"),
    ])

    # Other Windows locations
    paths_list.extend([
        os.path.join(user_home, "AppData", "Local", "Programs", "Claude", "claude.exe"),
        os.path.join(user_home, "AppData", "Roaming", "Claude", "claude.exe"),
    ])

    # System-wide locations (Unix-like)
    paths_list.extend([
        "/usr/local/bin/claude",
        "/opt/claude/claude",
    ])

    return paths_list


def find_claude_executable(
    *,
    test_execution: bool = False,
    return_none_if_not_found: bool = False,
    fast_mode: bool = True,
) -> Optional[str]:
    """Find Claude Code CLI executable with flexible options.

    Args:
        test_execution: If True, test that the executable actually works
        return_none_if_not_found: If True, return None instead of raising FileNotFoundError
        fast_mode: If True, skip execution tests and just check file existence (default: True)

    Returns:
        Path to Claude executable, or None if not found and return_none_if_not_found=True

    Raises:
        FileNotFoundError: If Claude not found and return_none_if_not_found=False
    """
    search_paths = _get_claude_search_paths()

    for location in search_paths:
        if not location:
            continue

        claude_path = Path(location)

        # Check if file exists and is executable
        if not (claude_path.exists() and claude_path.is_file()):
            continue

        # On Unix-like systems, check if file is executable
        # On Windows, .exe files are automatically executable, so skip this check
        if (
            os.name != "nt"
            and hasattr(os, "access")
            and not os.access(claude_path, os.X_OK)
        ):
            continue

        # If testing execution is requested and fast mode is disabled, verify the executable works
        if test_execution and not fast_mode:
            try:
                # Test with a simple command that should exit quickly
                result = execute_command(
                    [str(claude_path), "--help"],
                    timeout_seconds=20,
                )
                # Accept both 0 (success) and 1 (help shown) as valid
                if result.return_code not in [0, 1]:
                    continue
            except (OSError, subprocess.SubprocessError, FileNotFoundError):
                # If testing fails, try the next location
                # OSError: File not executable, permission issues
                # SubprocessError: Process execution issues
                # FileNotFoundError: Executable disappeared between checks
                continue

        return str(claude_path)

    # No working Claude executable found
    if return_none_if_not_found:
        return None

    raise FileNotFoundError(
        "Claude Code CLI not found. Please ensure it's installed and accessible.\n"
        "Install with: npm install -g @anthropic-ai/claude-code\n"
        f"Searched locations: {[str(path) for path in search_paths]}"
    )


def setup_claude_path() -> Optional[str]:
    """Setup PATH to include Claude CLI location if found.

    This function attempts to find Claude CLI and temporarily add its directory
    to PATH for the current process if it's not already accessible.

    Returns:
        Path to Claude executable if found and added to PATH, None otherwise
    """
    # Check if claude is already in PATH
    if shutil.which("claude"):
        return shutil.which("claude")

    # Try to find Claude CLI
    claude_path = find_claude_executable(return_none_if_not_found=True)
    if claude_path:
        # Add the directory containing Claude to PATH
        claude_dir = os.path.dirname(claude_path)
        current_path = os.environ.get("PATH", "")
        if claude_dir not in current_path:
            os.environ["PATH"] = f"{claude_dir}{os.pathsep}{current_path}"
        return claude_path

    return None


def verify_claude_installation() -> dict[str, Any]:
    """Verify Claude Code installation and return detailed information.

    Returns:
        Dictionary with installation details:
        {
            'found': bool,
            'path': str | None,
            'version': str | None,
            'works': bool,
            'error': str | None
        }
    """
    result: dict[str, Any] = {
        "found": False,
        "path": None,
        "version": None,
        "works": False,
        "error": None,
    }

    try:
        # Find the executable (disable fast mode for thorough verification)
        claude_path = find_claude_executable(test_execution=True, fast_mode=False)
        result["found"] = True
        result["path"] = claude_path

        # Get version information using simple subprocess to avoid complex runner issues
        try:
            # First try with our complex runner
            version_result = execute_command(
                [str(claude_path), "--version"],
                timeout_seconds=20,
            )
            if version_result.return_code == 0 and version_result.stdout.strip():
                result["version"] = version_result.stdout.strip()
                result["works"] = True
            else:
                # If complex runner fails, try simple subprocess as fallback
                try:
                    simple_result = subprocess.run(
                        [str(claude_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=None,  # Use current directory
                        env=None,  # Use current environment
                        check=False,
                    )
                    if simple_result.returncode == 0 and simple_result.stdout.strip():
                        result["version"] = simple_result.stdout.strip()
                        result["works"] = True
                    else:
                        result["error"] = (
                            f"Version check failed: {simple_result.stderr or version_result.stderr or 'No output'}"
                        )
                except Exception as fallback_e:
                    result["error"] = (
                        f"Version check failed: {version_result.stderr} (fallback: {fallback_e})"
                    )
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            # Try simple subprocess as final fallback
            try:
                simple_result = subprocess.run(
                    [str(claude_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if simple_result.returncode == 0 and simple_result.stdout.strip():
                    result["version"] = simple_result.stdout.strip()
                    result["works"] = True
                else:
                    result["error"] = (
                        f"Version check error: {e} (simple fallback: {simple_result.stderr or 'No output'})"
                    )
            except Exception as final_e:
                result["error"] = (
                    f"Version check error: {e} (final fallback: {final_e})"
                )

    except FileNotFoundError as e:
        result["error"] = str(e)
    except (OSError, subprocess.SubprocessError) as e:
        result["error"] = f"Process execution error: {e}"
    except (TypeError, ValueError) as e:
        result["error"] = f"Configuration error: {e}"

    return result
