"""isort formatter implementation with directory-based approach.

Based on Step 2 requirements, this module implements isort formatting using:
- Directory-based execution (pass directories directly to isort CLI)
- Output parsing to determine changed files from isort stdout
- Eliminates custom file discovery, letting isort handle file scanning
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_coder.utils.subprocess_runner import execute_command

from .models import FormatterResult
from .utils import get_default_target_dirs, read_tool_config


def format_with_isort(
    project_root: Path, target_dirs: Optional[List[str]] = None
) -> FormatterResult:
    """Format imports using directory-based isort CLI approach.

    Args:
        project_root: Root directory of the project
        target_dirs: Optional list of directories to format, defaults to auto-detection

    Returns:
        FormatterResult with success status and changed file list
    """
    try:
        # Read isort configuration
        config = _get_isort_config(project_root)

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
            changed_files = _format_isort_directory(target_path, config)
            files_changed.extend(changed_files)

        return FormatterResult(
            success=True,
            files_changed=files_changed,
            formatter_name="isort",
            error_message=None,
        )

    except (OSError, ValueError, RuntimeError) as e:
        return FormatterResult(
            success=False,
            files_changed=[],
            formatter_name="isort",
            error_message=f"isort formatting error: {str(e)}",
        )


def _get_isort_config(project_root: Path) -> Dict[str, Any]:
    """Read isort configuration using shared utility.

    Args:
        project_root: Root directory to search for pyproject.toml

    Returns:
        Dictionary with isort configuration, using defaults if not found
    """
    defaults = {"profile": "black", "line_length": 88, "float_to_top": True}
    return read_tool_config(project_root, "isort", defaults)


def _format_isort_directory(target_path: Path, config: Dict[str, Any]) -> List[str]:
    """Format directory and return list of changed files from parsed output.

    Args:
        target_path: Path to the directory to format
        config: isort configuration dictionary

    Returns:
        List of file paths that were reformatted

    Raises:
        Exception: If isort command fails with syntax errors or other issues
    """
    # Build isort format command for directory
    command = ["isort", str(target_path)]

    # Add configuration options
    command.extend(["--profile", config["profile"]])
    command.extend(["--line-length", str(config["line_length"])])
    if config["float_to_top"]:
        command.append("--float-to-top")

    # Execute isort formatting on directory
    result = execute_command(command)

    if result.return_code == 0:
        # No changes needed - return empty list
        return []
    elif result.return_code == 1:
        # Changes applied - parse output to get changed files
        return _parse_isort_output(result.stdout)
    else:
        # Syntax error or other failure (exit code 123+)
        raise RuntimeError(f"isort formatting failed: {result.stderr}")


def _parse_isort_output(stdout: str) -> List[str]:
    """Parse isort output to extract list of files that were fixed.

    Args:
        stdout: isort command stdout containing fixed file information

    Returns:
        List of file paths that were fixed
    """
    changed_files = []
    for line in stdout.strip().split("\n"):
        if line.startswith("Fixing "):
            # Extract filename from "Fixing /path/to/file.py"
            filename = line[7:]  # Remove "Fixing " prefix
            changed_files.append(filename)
    return changed_files
