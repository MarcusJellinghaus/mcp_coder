"""Cross-platform MCP server binary verification.

Provides generic verification of MCP server binaries — existence check
plus ``--version`` capture. Used by ``llm/env.py`` and ``icoder/env_setup.py``.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

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
