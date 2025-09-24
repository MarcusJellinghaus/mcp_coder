"""Black formatter implementation with directory-based approach.

Based on Step 1 requirements, this module implements Black formatting using:
- Directory-based execution (pass directories directly to Black CLI)
- Output parsing to determine changed files from Black stdout
- Eliminates custom file discovery, letting Black handle file scanning
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_coder.utils.subprocess_runner import execute_command

from .models import FormatterResult
from .utils import get_default_target_dirs, read_tool_config


def format_with_black(
    project_root: Path, target_dirs: Optional[List[str]] = None
) -> FormatterResult:
    """Format code using directory-based Black CLI approach.

    Args:
        project_root: Root directory of the project
        target_dirs: Optional list of directories to format, defaults to auto-detection

    Returns:
        FormatterResult with success status and changed file list
    """
    try:
        # Read Black configuration
        config = _get_black_config(project_root)

        # Determine target directories if not provided
        if target_dirs is None:
            target_dirs = get_default_target_dirs(project_root)

        # Track files that were changed across all directories
        files_changed = []

        # Process each target directory using directory-based approach
        for target_dir in target_dirs:
            target_path = project_root / target_dir
            if not target_path.exists():
                continue

            # Format entire directory and get list of changed files
            changed_files = _format_black_directory(target_path, config)
            files_changed.extend(changed_files)

        return FormatterResult(
            success=True,
            files_changed=files_changed,
            formatter_name="black",
            error_message=None,
        )

    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        return FormatterResult(
            success=False,
            files_changed=[],
            formatter_name="black",
            error_message=f"Black formatting error: {str(e)}",
        )


def _get_black_config(project_root: Path) -> Dict[str, Any]:
    """Read Black configuration using shared utility.

    Args:
        project_root: Root directory to search for pyproject.toml

    Returns:
        Dictionary with Black configuration, using defaults if not found
    """
    defaults = {"line-length": 88, "target-version": ["py311"]}
    return read_tool_config(project_root, "black", defaults)


def _format_black_directory(target_path: Path, config: Dict[str, Any]) -> List[str]:
    """Format directory and return list of changed files from parsed output.

    Args:
        target_path: Path to the directory to format
        config: Black configuration dictionary

    Returns:
        List of file paths that were reformatted

    Raises:
        Exception: If Black command fails with syntax errors or other issues
    """
    # Build Black format command for directory
    command = ["black", str(target_path)]

    # Add configuration options
    command.extend(["--line-length", str(config["line-length"])])
    for target_version in config["target-version"]:
        command.extend(["--target-version", target_version])

    # Execute Black formatting on directory
    result = execute_command(command)

    if result.return_code == 0:
        # Success - parse stderr output to get changed files (Black outputs to stderr)
        return _parse_black_output(result.stderr)
    else:
        # Syntax error or other failure
        raise subprocess.CalledProcessError(result.return_code, command, result.stderr)


def _parse_black_output(stderr: str) -> List[str]:
    """Parse Black output to extract list of files that were reformatted.

    Args:
        stderr: Black command stderr containing reformatted file information

    Returns:
        List of file paths that were reformatted
    """
    changed_files = []
    for line in stderr.strip().split("\n"):
        if line.startswith("reformatted "):
            # Extract filename from "reformatted /path/to/file.py"
            filename = line[12:]  # Remove "reformatted " prefix
            changed_files.append(filename)
    return changed_files
