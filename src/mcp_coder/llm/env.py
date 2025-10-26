"""Environment variable preparation for LLM subprocess execution.

This module provides utilities for preparing environment variables that
enable portable .mcp.json configuration files across different machines.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


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

    # Get runner environment (where mcp-coder is currently executing)
    # Priority: VIRTUAL_ENV > CONDA_PREFIX > sys.prefix
    runner_venv = os.environ.get("VIRTUAL_ENV")
    if not runner_venv:
        runner_venv = os.environ.get("CONDA_PREFIX")
    if not runner_venv:
        runner_venv = sys.prefix
    
    logger.debug("Detected runner environment: %s", runner_venv)

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
