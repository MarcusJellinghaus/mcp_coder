"""Cross-platform MCP server binary verification.

Provides generic verification of MCP server binaries — existence check
plus ``--version`` capture. Used by ``llm/env.py`` and ``icoder/env_setup.py``.
"""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.utils.subprocess_runner import execute_command

from .toolkit_runner import WORKSPACE_SERVER, llm_permissions, mcp_servers_of

logger = logging.getLogger(__name__)

# Servers whose binaries ship with the tool env; toolkit servers are optional
_SHIPPED_SERVERS: tuple[str, ...] = (WORKSPACE_SERVER,)


def required_mcp_servers(project_dir: Path) -> list[str]:
    """MCP servers the session needs: mcp-workspace plus the toolkit's.

    Args:
        project_dir: Project root containing the toolkit config.

    Returns:
        ``"mcp-workspace"`` first, then the servers the configured toolkit
        grants tools of, sorted. Only ``"mcp-workspace"`` when the toolkit
        fails to load.
    """
    return mcp_servers_of(llm_permissions(project_dir, "claude"))


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
    """Verify the shipped MCP server binaries exist and capture their versions.

    Only ``mcp-workspace`` is checked; toolkit servers are optional installs.

    Returns:
        List of MCPServerInfo with name, path, and version for each server.

    Raises:
        FileNotFoundError: If a binary is missing.
        RuntimeError: If a binary exists but ``--version`` times out,
            cannot be launched, or exits non-zero.
    """
    timeout = 30
    bin_dir = get_bin_dir(venv_root)
    results: list[MCPServerInfo] = []
    for name in _SHIPPED_SERVERS:
        exe_path = bin_dir / _exe_name(name)
        if not exe_path.exists():
            raise FileNotFoundError(f"{_exe_name(name)} not found in {bin_dir}")
        result = execute_command([str(exe_path), "--version"], timeout_seconds=timeout)
        if result.timed_out:
            raise RuntimeError(f"{exe_path} --version timed out after {timeout}s")
        if result.execution_error:
            raise RuntimeError(f"Failed to invoke {exe_path}: {result.execution_error}")
        if result.return_code != 0:
            raise RuntimeError(
                f"{exe_path} --version exited with code {result.return_code}: "
                f"{result.stderr.strip()}"
            )
        version = result.stdout.strip()
        results.append(MCPServerInfo(name=name, path=exe_path, version=version))
    return results


# Regex pattern for parsing `claude mcp list` output lines.
# Matches: "server-name: /path/to/exe args - ✓ Connected"
#   Group 1: server name (e.g., "mcp-tools-py")
#   Group 2: status icon (e.g., "✓", "✗", "!")
#   Group 3: status text (e.g., "Connected", "Failed to start")
_MCP_LIST_LINE_RE = re.compile(r"^(\S+):\s+.+\s+-\s+(\S+)\s+(.+)$")


@dataclass(frozen=True)
class ClaudeMCPStatus:
    """Connection status for an MCP server from ``claude mcp list``."""

    name: str
    """Required server name (e.g. ``mcp-workspace``)."""

    status_text: str
    """Raw status text from claude output (e.g. ``Connected``), or
    ``not listed`` when the server is missing from the output."""

    ok: bool
    """True when status_text == ``Connected``."""


def parse_claude_mcp_list(
    env_vars: dict[str, str],
    required_servers: Sequence[str],
    mcp_config_path: str = ".mcp.json",
    timeout: int = 60,
    claude_executable: str | None = None,
) -> list[ClaudeMCPStatus] | None:
    """Run ``claude mcp list`` and parse connection status for required servers.

    Args:
        env_vars: Environment variables for subprocess
            (for ``.mcp.json`` variable resolution).
        required_servers: Servers to report on, e.g. from required_mcp_servers.
        mcp_config_path: Path to MCP config file (default: ``".mcp.json"``).
        timeout: Subprocess timeout in seconds (default: 60).
        claude_executable: Path to the Claude CLI binary. When ``None``
            the check is skipped and the function returns ``None``.

    Returns:
        One ClaudeMCPStatus per required server, in ``required_servers``
        order; a server missing from the output is ``not listed`` with
        ``ok=False``. None on any failure.
    """
    if claude_executable is None:
        logger.debug("Claude executable not provided; skipping MCP list")
        return None

    command = [
        claude_executable,
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

    found: dict[str, ClaudeMCPStatus] = {}
    for line in result.stdout.splitlines():
        match = _MCP_LIST_LINE_RE.match(line.strip())
        if not match:
            continue
        raw_name = match.group(1)
        status_text = match.group(3).strip()
        if raw_name in required_servers:
            found[raw_name] = ClaudeMCPStatus(
                name=raw_name,
                status_text=status_text,
                ok=status_text == "Connected",
            )

    return [
        found.get(name) or ClaudeMCPStatus(name, "not listed", False)
        for name in required_servers
    ]
