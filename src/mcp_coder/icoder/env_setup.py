"""iCoder-specific environment setup and RuntimeInfo.

Pure function: computes tool env, project venv, assembles env vars, verifies
MCP binaries, and returns a ``RuntimeInfo`` dataclass.  **No os.environ
mutation.**  Env vars flow to the Claude subprocess because the caller passes
``runtime_info.env_vars`` into ``RealLLMService``, which merges them with
``os.environ`` in ``subprocess_runner.prepare_env()``.
"""

from __future__ import annotations

import importlib.metadata
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
)
from mcp_coder.utils.mcp_verification import (
    MCPServerInfo,
    get_bin_dir,
    verify_mcp_servers,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeInfo:
    """Runtime information gathered during iCoder startup."""

    mcp_coder_version: str
    python_version: str
    claude_code_version: str
    tool_env_path: str
    project_venv_path: str
    project_dir: str
    env_vars: dict[str, str]
    mcp_servers: list[MCPServerInfo]


def _get_claude_code_version() -> str:
    """Get Claude Code CLI version string.

    Returns ``"unknown"`` if Claude cannot be found or queried.

    Returns:
        Version string from ``claude --version``, or ``"unknown"`` on failure.
    """
    try:
        from mcp_coder.utils.subprocess_runner import execute_command

        claude_path = find_claude_executable(return_none_if_not_found=True)
        if claude_path is None:
            return "unknown"
        result = execute_command(
            [claude_path, "--version"],
            timeout_seconds=15,
        )
        if result.return_code == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    return "unknown"


def setup_icoder_environment(project_dir: Path) -> RuntimeInfo:
    """Set up iCoder environment: compute paths, verify MCP servers, return RuntimeInfo.

    Pure function — does NOT mutate ``os.environ``.  Env vars are available to
    subprocesses because the caller passes ``runtime_info.env_vars`` into
    ``RealLLMService``, which merges with ``os.environ`` in ``prepare_env()``.

    Returns:
        RuntimeInfo with resolved paths, environment variables, and MCP server details.
    """
    tool_env = sys.prefix
    bin_dir = get_bin_dir(Path(tool_env))

    project_venv = project_dir / ".venv"
    if not project_venv.exists():
        logger.info(
            "No project .venv found at %s — using tool environment for both.",
            project_venv,
        )
        project_venv = Path(tool_env)

    computed = {
        "MCP_CODER_VENV_PATH": str(bin_dir),
        "MCP_CODER_VENV_DIR": str(tool_env),
        "MCP_CODER_PROJECT_DIR": str(project_dir),
    }

    effective: dict[str, str] = {}
    for key, value in computed.items():
        existing = os.environ.get(key)
        if existing is None:
            effective[key] = value
        else:
            if existing != value:
                logger.debug(
                    "%s already set to %s (computed: %s)", key, existing, value
                )
            effective[key] = existing

    mcp_servers = verify_mcp_servers(tool_env)
    version = importlib.metadata.version("mcp-coder")
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    claude_code_version = _get_claude_code_version()

    return RuntimeInfo(
        mcp_coder_version=version,
        python_version=python_version,
        claude_code_version=claude_code_version,
        tool_env_path=str(tool_env),
        project_venv_path=str(project_venv),
        project_dir=str(project_dir),
        env_vars=effective,
        mcp_servers=mcp_servers,
    )
