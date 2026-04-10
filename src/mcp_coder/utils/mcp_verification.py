"""Cross-platform MCP server binary verification.

Provides generic verification of MCP server binaries — existence check
plus ``--version`` capture. Used by ``llm/env.py`` and ``icoder/env_setup.py``.
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
)
from mcp_coder.utils.subprocess_runner import execute_command

logger = logging.getLogger(__name__)

MCP_SERVER_NAMES: list[str] = ["mcp-tools-py", "mcp-workspace"]


def get_bin_dir(venv_root: str | Path) -> Path:
    """Return the platform-appropriate bin directory for a venv.

    Returns ``Scripts`` on Windows, ``bin`` on POSIX.
    """
    subdir = "Scripts" if sys.platform == "win32" else "bin"
    return Path(venv_root) / subdir


def _exe_name(name: str) -> str:
    """Return *name*.exe on Windows, *name* on POSIX."""
    return f"{name}.exe" if sys.platform == "win32" else name


@dataclass(frozen=True)
class MCPServerInfo:
    """Verified MCP server binary info."""

    name: str
    path: Path
    version: str


def verify_mcp_servers(venv_root: str | Path) -> list[MCPServerInfo]:
    """Verify MCP server binaries exist and capture their versions.

    Returns:
        List of MCPServerInfo with name, path, and version for each server.

    Raises:
        FileNotFoundError: If a binary is missing.
        RuntimeError: If a binary exists but ``--version`` fails
            (OSError/FileNotFoundError from subprocess, or non-zero returncode).
    """
    bin_dir = get_bin_dir(venv_root)
    results: list[MCPServerInfo] = []
    for name in MCP_SERVER_NAMES:
        exe_path = bin_dir / _exe_name(name)
        if not exe_path.exists():
            raise FileNotFoundError(f"{_exe_name(name)} not found in {bin_dir}")
        try:
            proc = subprocess.run(
                [str(exe_path), "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
        except (FileNotFoundError, OSError) as e:
            raise RuntimeError(f"Failed to invoke {exe_path}: {e}") from e
        if proc.returncode != 0:
            raise RuntimeError(
                f"{exe_path} --version exited with code {proc.returncode}: "
                f"{proc.stderr.strip()}"
            )
        version = proc.stdout.strip()
        results.append(MCPServerInfo(name=name, path=exe_path, version=version))
    return results


# Regex pattern for parsing `claude mcp list` output lines.
# Matches: "server-name: /path/to/exe args - ✓ Connected"
#   Group 1: server name (e.g., "tools-py")
#   Group 2: status icon (e.g., "✓", "✗", "!")
#   Group 3: status text (e.g., "Connected", "Failed to start")
_MCP_LIST_LINE_RE = re.compile(r"^(\S+):\s+.+\s+-\s+(\S+)\s+(.+)$")


@dataclass(frozen=True)
class ClaudeMCPStatus:
    """Connection status for an MCP server from ``claude mcp list``."""

    name: str
    """Canonical name from MCP_SERVER_NAMES (e.g. ``mcp-tools-py``)."""

    status_text: str
    """Raw status text from claude output (e.g. ``Connected``)."""

    ok: bool
    """True when status_text == ``Connected``."""


def parse_claude_mcp_list(
    env_vars: dict[str, str],
    mcp_config_path: str = ".mcp.json",
    timeout: int = 60,
) -> list[ClaudeMCPStatus] | None:
    """Run ``claude mcp list`` and parse connection status for known servers.

    Args:
        env_vars: Environment variables for subprocess
            (for ``.mcp.json`` variable resolution).
        mcp_config_path: Path to MCP config file (default: ``".mcp.json"``).
        timeout: Subprocess timeout in seconds (default: 60).

    Returns:
        List of ClaudeMCPStatus for servers in MCP_SERVER_NAMES,
        or None on any failure.
    """
    claude_path = find_claude_executable(return_none_if_not_found=True)
    if claude_path is None:
        logger.debug("Claude executable not found; skipping MCP list")
        return None

    command = [
        claude_path,
        "--mcp-config",
        mcp_config_path,
        "--strict-mcp-config",
        "mcp",
        "list",
    ]

    try:
        result = execute_command(
            command,
            timeout_seconds=timeout,
            env=env_vars,
        )
    except Exception:
        logger.debug("Exception running claude mcp list", exc_info=True)
        return None

    if result.timed_out:
        logger.debug("claude mcp list timed out")
        return None

    if result.return_code != 0:
        logger.debug(
            "claude mcp list exited with code %d: %s",
            result.return_code,
            result.stderr,
        )
        return None

    statuses: list[ClaudeMCPStatus] = []
    for line in result.stdout.splitlines():
        match = _MCP_LIST_LINE_RE.match(line.strip())
        if not match:
            continue
        raw_name = match.group(1)
        status_text = match.group(3).strip()
        canonical_name = f"mcp-{raw_name}"
        if canonical_name in MCP_SERVER_NAMES:
            statuses.append(
                ClaudeMCPStatus(
                    name=canonical_name,
                    status_text=status_text,
                    ok=status_text == "Connected",
                )
            )

    return statuses
