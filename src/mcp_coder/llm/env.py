"""Environment variable preparation for LLM subprocess execution.

This module provides utilities for preparing environment variables that
enable portable .mcp.json configuration files across different machines.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_runner_environment() -> tuple[str, str]:
    """Get runner environment path and source name.

    Returns:
        Tuple of (environment_path, source_name)

    Priority: VIRTUAL_ENV > CONDA_PREFIX > sys.prefix
    Invalid paths trigger fallback to next option with warning.
    """
    # Try VIRTUAL_ENV first
    virtual_env = os.environ.get("VIRTUAL_ENV", "").strip()
    if virtual_env and Path(virtual_env).exists():
        return virtual_env, "VIRTUAL_ENV"
    elif virtual_env:
        logger.warning(
            "VIRTUAL_ENV points to non-existent path: %s, trying next option",
            virtual_env,
        )

    # Try CONDA_PREFIX second
    conda_prefix = os.environ.get("CONDA_PREFIX", "").strip()
    if conda_prefix and Path(conda_prefix).exists():
        return conda_prefix, "CONDA_PREFIX"
    elif conda_prefix:
        logger.warning(
            "CONDA_PREFIX points to non-existent path: %s, using sys.prefix",
            conda_prefix,
        )

    # Fall back to sys.prefix (always valid)
    return sys.prefix, "sys.prefix"


def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare MCP_CODER_* environment variables for LLM subprocess.

    This function prepares environment variables that can be used in .mcp.json
    configuration files to make them portable across different machines.

    The runner environment (MCP_CODER_VENV_DIR) is where mcp-coder is currently
    executing, detected from VIRTUAL_ENV, CONDA_PREFIX, or sys.prefix.

    Args:
        project_dir: Absolute path to project directory

    Returns:
        Dictionary with MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
        environment variables as absolute OS-native paths.
    """
    logger.debug("Preparing LLM environment for project: %s", project_dir)

    # Get runner environment with validation and source tracking
    runner_venv, source = _get_runner_environment()

    logger.debug("Detected runner environment from %s: %s", source, runner_venv)

    # Convert paths to absolute OS-native strings
    project_dir_absolute = str(Path(project_dir).resolve())
    venv_dir_absolute = str(Path(runner_venv).resolve())

    env_vars = {
        "MCP_CODER_PROJECT_DIR": project_dir_absolute,
        "MCP_CODER_VENV_DIR": venv_dir_absolute,
    }

    logger.debug(
        "Prepared environment variables: MCP_CODER_PROJECT_DIR=%s, MCP_CODER_VENV_DIR=%s",
        project_dir_absolute,
        venv_dir_absolute,
    )

    return env_vars
