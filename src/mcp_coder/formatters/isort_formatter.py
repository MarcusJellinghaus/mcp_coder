"""isort formatter implementation with exit code change detection.

Based on Step 0 analysis findings, this module implements isort formatting using:
- Two-phase approach (check first, format if needed)
- Exit code change detection (0=no changes, 1=changes needed)
- Inline configuration reading using tomllib patterns
"""

import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_coder.formatters import FormatterResult
from mcp_coder.utils.subprocess_runner import execute_command


def format_with_isort(
    project_root: Path, target_dirs: Optional[List[str]] = None
) -> FormatterResult:
    """Format imports using proven isort CLI patterns with exit code detection.

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
            target_dirs = _get_default_target_dirs(project_root)

        # Track files that were changed
        files_changed = []

        # Process each target directory
        for target_dir in target_dirs:
            target_path = project_root / target_dir
            if not target_path.exists():
                continue

            # Find Python files to process
            python_files = _find_python_files(target_path)

            for file_path in python_files:
                # Check if import sorting is needed
                if _check_isort_changes(str(file_path), config):
                    # Apply import sorting
                    if _apply_isort_formatting(str(file_path), config):
                        files_changed.append(str(file_path))
                    else:
                        # Formatting failed
                        return FormatterResult(
                            success=False,
                            files_changed=[],
                            formatter_name="isort",
                            error_message=f"Failed to format imports in {file_path}",
                        )

        return FormatterResult(
            success=True,
            files_changed=files_changed,
            formatter_name="isort",
            error_message=None,
        )

    except Exception as e:
        return FormatterResult(
            success=False,
            files_changed=[],
            formatter_name="isort",
            error_message=f"isort formatting error: {str(e)}",
        )


def _get_isort_config(project_root: Path) -> Dict[str, Any]:
    """Read isort configuration inline using validated tomllib patterns.

    Args:
        project_root: Root directory to search for pyproject.toml

    Returns:
        Dictionary with isort configuration, using defaults if not found
    """
    # Default isort configuration with Black compatibility
    config = {"profile": "black", "line_length": 88, "float_to_top": True}

    # Try to read from pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)

            # Extract isort configuration
            isort_config = pyproject_data.get("tool", {}).get("isort", {})

            # Update config with values from pyproject.toml
            if "profile" in isort_config:
                config["profile"] = isort_config["profile"]
            if "line_length" in isort_config:
                config["line_length"] = isort_config["line_length"]
            if "float_to_top" in isort_config:
                config["float_to_top"] = isort_config["float_to_top"]

        except (tomllib.TOMLDecodeError, OSError):
            # Use defaults if file can't be read
            pass

    return config


def _check_isort_changes(file_path: str, config: Dict[str, Any]) -> bool:
    """Check if isort formatting needed using --check-only (exit code pattern).

    Args:
        file_path: Path to the Python file to check
        config: isort configuration dictionary

    Returns:
        True if formatting is needed, False if already sorted

    Raises:
        Exception: If isort check command fails with syntax errors
    """
    # Build isort check command
    command = ["isort", "--check-only", file_path]

    # Add configuration options
    command.extend(["--profile", config["profile"]])
    command.extend(["--line-length", str(config["line_length"])])
    if config["float_to_top"]:
        command.append("--float-to-top")

    # Execute isort check
    result = execute_command(command)

    if result.return_code == 0:
        # No changes needed
        return False
    elif result.return_code == 1:
        # Changes needed (this is isort's way to indicate imports need sorting)
        return True
    else:
        # Syntax error or other failure
        raise Exception(f"isort check failed: {result.stderr}")


def _apply_isort_formatting(file_path: str, config: Dict[str, Any]) -> bool:
    """Apply isort formatting and return success status.

    Args:
        file_path: Path to the Python file to format
        config: isort configuration dictionary

    Returns:
        True if formatting succeeded, False otherwise
    """
    # Build isort format command
    command = ["isort", file_path]

    # Add configuration options
    command.extend(["--profile", config["profile"]])
    command.extend(["--line-length", str(config["line_length"])])
    if config["float_to_top"]:
        command.append("--float-to-top")

    # Execute isort formatting
    result = execute_command(command)

    # Return success status (exit 0 = success)
    return result.return_code == 0


def _get_default_target_dirs(project_root: Path) -> List[str]:
    """Get default target directories for import sorting.

    Args:
        project_root: Root directory of the project

    Returns:
        List of directory names to format
    """
    target_dirs = []

    # Check if "src" directory exists
    if (project_root / "src").exists():
        target_dirs.append("src")

    # Check if "tests" directory exists
    if (project_root / "tests").exists():
        target_dirs.append("tests")

    # If neither exists, default to current directory
    if not target_dirs:
        target_dirs.append(".")

    return target_dirs


def _find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory recursively.

    Args:
        directory: Directory to search for Python files

    Returns:
        List of Python file paths
    """
    python_files = []

    if directory.is_file() and directory.suffix == ".py":
        python_files.append(directory)
    elif directory.is_dir():
        # Recursively find Python files
        for file_path in directory.rglob("*.py"):
            python_files.append(file_path)

    return python_files
