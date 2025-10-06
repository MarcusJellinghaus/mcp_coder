"""Environment variable preparation for LLM subprocess execution.

This module provides utilities for preparing environment variables that
enable portable .mcp.json configuration files across different machines.
"""

import logging
from pathlib import Path

from ..utils.detection import detect_python_environment

logger = logging.getLogger(__name__)


def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare MCP_CODER_* environment variables for LLM subprocess.

    This function prepares environment variables that can be used in .mcp.json
    configuration files to make them portable across different machines.

    Args:
        project_dir: Absolute path to project directory

    Returns:
        Dictionary with MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
        environment variables as absolute OS-native paths.

    Raises:
        RuntimeError: If virtual environment not found
    """
    logger.debug("Preparing LLM environment for project: %s", project_dir)

    # Detect Python environment and virtual environment
    python_exe, venv_path = detect_python_environment(project_dir)

    # Strict requirement: venv must be found
    if venv_path is None:
        raise RuntimeError(
            f"No virtual environment found in {project_dir} and not running "
            "from a virtual environment.\n"
            "MCP Coder requires a venv to set MCP_CODER_VENV_DIR.\n"
            "Create one with: python -m venv .venv"
        )

    # Convert paths to absolute OS-native strings
    project_dir_absolute = str(Path(project_dir).resolve())
    venv_dir_absolute = str(Path(venv_path).resolve())

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
