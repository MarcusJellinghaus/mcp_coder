"""Environment variable preparation for LLM subprocess execution.

This module provides utilities for preparing environment variables that
enable portable .mcp.json configuration files across different machines.
"""

import logging
import os
import sys
from pathlib import Path

from mcp_coder.llm.claude_settings import MCP_TIMEOUT_MS
from mcp_coder.utils.mcp_verification import get_bin_dir

logger = logging.getLogger(__name__)


def _get_tool_environment() -> tuple[str, str]:
    """Get the tool environment root and the source it was resolved from.

    The "tool environment" is where mcp-coder *and the MCP server executables*
    (``mcp-tools-py``, ``mcp-workspace``) are installed. Because the servers are
    co-installed with mcp-coder, the reliable signal is the prefix of the
    **running** mcp-coder interpreter (``sys.prefix``) -- NOT ``VIRTUAL_ENV``.

    In the two-environment model a launcher activates the *project* venv
    (so ``VIRTUAL_ENV`` points at it, and pytest/mypy run against the project's
    Python) while mcp-coder itself runs from the tool env. ``VIRTUAL_ENV`` then
    points at the project venv, which need not contain the MCP server
    executables -- using it would make the servers fail to start. The project
    venv reaches the servers via ``${VIRTUAL_ENV}`` in ``.mcp.json`` (for
    ``--venv-path`` / ``--python-executable``), not through this value.

    Resolution order:
        1. A pre-set ``MCP_CODER_VENV_DIR`` (a two-env-aware launcher already
           pointed it at the tool env), if it exists.
        2. ``sys.prefix`` (the running mcp-coder interpreter).

    Returns:
        Tuple of (environment_path, source_name).
    """
    preset = os.environ.get("MCP_CODER_VENV_DIR", "").strip()
    if preset and Path(preset).exists():
        return preset, "MCP_CODER_VENV_DIR"
    if preset:
        logger.warning(
            "MCP_CODER_VENV_DIR points to non-existent path: %s, using sys.prefix",
            preset,
        )
    return sys.prefix, "sys.prefix"


def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare MCP_CODER_* environment variables for LLM subprocess.

    This function prepares environment variables that can be used in .mcp.json
    configuration files to make them portable across different machines.

    ``MCP_CODER_VENV_DIR`` / ``MCP_CODER_VENV_PATH`` point at the **tool env**
    (where mcp-coder and the MCP servers are installed), resolved from the
    running interpreter -- not from ``VIRTUAL_ENV``. See ``_get_tool_environment``
    for the rationale. The project's own Python is passed separately via
    ``${VIRTUAL_ENV}`` in ``.mcp.json``.

    Args:
        project_dir: Absolute path to project directory

    Returns:
        Dictionary with MCP_CODER_PROJECT_DIR, MCP_CODER_VENV_DIR,
        MCP_CODER_VENV_PATH, DISABLE_AUTOUPDATER, and MCP_TIMEOUT
        environment variables. MCP_CODER_VENV_PATH points to the tool env's
        Scripts (Windows) or bin (POSIX) subdirectory. A pre-set
        MCP_CODER_VENV_PATH is preserved (honoring a launcher-provided value);
        otherwise it is derived from the tool env. DISABLE_AUTOUPDATER defaults
        to "1" and MCP_TIMEOUT to "30000", each preserving any value already set
        in the parent environment.
    """
    logger.debug("Preparing LLM environment for project: %s", project_dir)

    # Tool env = where mcp-coder + the MCP servers live (running interpreter),
    # NOT the active VIRTUAL_ENV which may be the project venv.
    tool_env, source = _get_tool_environment()

    logger.debug("Detected tool environment from %s: %s", source, tool_env)

    # Convert paths to absolute OS-native strings
    project_dir_absolute = str(Path(project_dir).resolve())
    venv_dir_absolute = str(Path(tool_env).resolve())

    # Honor a launcher-provided bin dir (same contract as MCP_TIMEOUT); else
    # derive it from the tool env.
    preset_path = os.environ.get("MCP_CODER_VENV_PATH", "").strip()
    if preset_path:
        venv_path = str(Path(preset_path).resolve())
    else:
        venv_path = str(get_bin_dir(Path(tool_env)).resolve())

    env_vars = {
        "MCP_CODER_PROJECT_DIR": project_dir_absolute,
        "MCP_CODER_VENV_DIR": venv_dir_absolute,
        "MCP_CODER_VENV_PATH": venv_path,
    }

    env_vars["DISABLE_AUTOUPDATER"] = os.environ.get("DISABLE_AUTOUPDATER", "1")
    env_vars["MCP_TIMEOUT"] = os.environ.get("MCP_TIMEOUT", MCP_TIMEOUT_MS)

    logger.debug(
        "Prepared environment variables: MCP_CODER_PROJECT_DIR=%s, "
        "MCP_CODER_VENV_DIR=%s, MCP_CODER_VENV_PATH=%s",
        project_dir_absolute,
        venv_dir_absolute,
        venv_path,
    )

    return env_vars
