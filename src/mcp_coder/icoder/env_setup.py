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
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
)
from mcp_coder.utils.mcp_verification import (
    ClaudeMCPStatus,
    MCPServerInfo,
    parse_claude_mcp_list,
    verify_mcp_servers,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeInfo:
    """Runtime information gathered during iCoder startup."""

    mcp_coder_version: str
    mcp_coder_utils_version: str
    python_version: str
    claude_code_version: str
    tool_env_path: str
    project_venv_path: str
    project_dir: str
    env_vars: dict[str, str]
    mcp_servers: list[MCPServerInfo]
    mcp_connection_status: list[ClaudeMCPStatus] | None = None
    mcp_tools_exposed: int | None = None
    mcp_tools_status: str | None = None


def _get_package_version(name: str) -> str:
    """Return installed version of ``name``, or ``"unknown"`` if not found."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


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


def _probe_exposed_mcp_tools(
    provider: str,
    mcp_config: str | None,
    env_vars: dict[str, str],
    execution_dir: str,
) -> tuple[str | None, int | None]:
    """Return (status, count) via one short 'Reply with OK' prompt; (None, None) on any failure.

    Claude-only: any other provider returns ``(None, None)`` without prompting.
    Sends a single short prompt, reads the init ``system`` event, derives a
    coarse status (``fatal`` > ``pending`` > ``connected``) and counts the
    exposed ``mcp__*`` tools. The whole body is guarded — any failure returns
    ``(None, None)`` and logs at debug — so this never blocks iCoder launch.

    Returns:
        ``(status, count)`` on success, else ``(None, None)``.
    """
    if provider != "claude":
        return (None, None)
    try:
        from mcp_coder.llm.interface import prompt_llm
        from mcp_coder.llm.providers.claude.claude_mcp_guard import (
            find_exposed_mcp_tools,
            find_fatal_mcp_servers,
            find_unavailable_mcp_servers,
        )

        resp = prompt_llm(
            "Reply with OK",
            provider="claude",
            timeout=30,
            mcp_config=mcp_config,
            env_vars=env_vars,
            execution_dir=execution_dir,
        )
        raw_response = cast(dict[str, Any], resp.get("raw_response", {}))
        system_message = cast(Any, raw_response.get("system"))
        if find_fatal_mcp_servers(system_message):
            status = "fatal"
        elif find_unavailable_mcp_servers(system_message):
            status = "pending"
        else:
            status = "connected"
        count = len(find_exposed_mcp_tools(system_message))
        return (status, count)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("MCP tool probe failed", exc_info=True)
        return (None, None)


def setup_icoder_environment(
    project_dir: Path,
    provider: str = "claude",
    mcp_config: str | None = None,
) -> RuntimeInfo:
    """Set up iCoder environment: compute paths, verify MCP servers, return RuntimeInfo.

    Pure function — does NOT mutate ``os.environ``.  Env vars are available to
    subprocesses because the caller passes ``runtime_info.env_vars`` into
    ``RealLLMService``, which merges with ``os.environ`` in ``prepare_env()``.

    Returns:
        RuntimeInfo with resolved paths, environment variables, and MCP server details.
    """
    # Reuse shared env var logic (VIRTUAL_ENV > CONDA_PREFIX > sys.prefix)
    effective = prepare_llm_environment(project_dir)

    tool_env = effective["MCP_CODER_VENV_DIR"]

    project_venv = project_dir / ".venv"
    if not project_venv.exists():
        logger.info(
            "No project .venv found at %s — using tool environment for both.",
            project_venv,
        )
        project_venv = Path(tool_env)

    mcp_servers = verify_mcp_servers(tool_env)

    # Connection status from claude mcp list (graceful fallback)
    claude_exe = find_claude_executable(return_none_if_not_found=True)
    mcp_connection_status = parse_claude_mcp_list(
        env_vars=effective, claude_executable=claude_exe
    )

    mcp_coder_version = _get_package_version("mcp-coder")
    mcp_coder_utils_version = _get_package_version("mcp-coder-utils")
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    claude_code_version = _get_claude_code_version()

    mcp_tools_status, mcp_tools_exposed = _probe_exposed_mcp_tools(
        provider=provider,
        mcp_config=mcp_config,
        env_vars=effective,
        execution_dir=str(project_dir),
    )

    return RuntimeInfo(
        mcp_coder_version=mcp_coder_version,
        mcp_coder_utils_version=mcp_coder_utils_version,
        python_version=python_version,
        claude_code_version=claude_code_version,
        tool_env_path=str(tool_env),
        project_venv_path=str(project_venv),
        project_dir=str(project_dir),
        env_vars=effective,
        mcp_servers=mcp_servers,
        mcp_connection_status=mcp_connection_status,
        mcp_tools_exposed=mcp_tools_exposed,
        mcp_tools_status=mcp_tools_status,
    )
