"""Black formatter implementation with stdout parsing for change detection."""

import re
from pathlib import Path
from typing import List, Optional

from ..utils.subprocess_runner import execute_command
from .config_reader import get_black_config
from .models import FileChange, FormatterConfig, FormatterResult


def format_with_black(
    project_root: Path, target_dirs: Optional[List[str]] = None
) -> FormatterResult:
    """Format code using Black and return detailed results.

    Args:
        project_root: Root directory of the project
        target_dirs: Optional list of target directory names to format

    Returns:
        FormatterResult with success status and list of changed files
    """
    # Load Black configuration
    config = get_black_config(project_root)

    # Override target directories if specified
    if target_dirs is not None:
        config.target_directories = [
            project_root / dir_name
            for dir_name in target_dirs
            if (project_root / dir_name).exists()
        ]

    # Get list of Python files
    python_files = _get_python_files(config.target_directories)

    # If no Python files found, return success with empty changes
    if not python_files:
        return FormatterResult(
            success=True,
            files_changed=[],
            execution_time_ms=0,
            formatter_name="black",
            error_message=None,
        )

    # Build and execute Black command
    command = _build_black_command(config)
    result = execute_command(command, cwd=str(project_root))

    # Parse Black output to find reformatted files
    # Black outputs to both stdout and stderr, so check both
    combined_output = result.stdout + "\n" + result.stderr
    reformatted_files = _parse_black_output(combined_output, project_root)
    reformatted_paths = set(reformatted_files)

    # Create FileChange objects for all Python files
    files_changed = [
        FileChange(
            file_path=file_path,
            had_changes=file_path in reformatted_paths,
        )
        for file_path in python_files
    ]

    # Determine success and error message
    success = result.return_code == 0
    error_message = None

    if not success:
        if result.timed_out:
            error_message = result.execution_error or "Black formatting timed out"
        else:
            error_message = result.stderr.strip() or "Black formatting failed"

    return FormatterResult(
        success=success,
        files_changed=files_changed,
        execution_time_ms=result.execution_time_ms or 0,
        formatter_name="black",
        error_message=error_message,
    )


def _get_python_files(target_directories: List[Path]) -> List[Path]:
    """Get all Python files in the target directories.

    Note: This will be moved to utils.py in step 5 for reuse by isort.

    Args:
        target_directories: List of directories to search for Python files

    Returns:
        List of Python file paths found in the directories
    """
    python_files = []

    for directory in target_directories:
        if not directory.exists() or not directory.is_dir():
            continue

        # Recursively find all .py files, excluding __pycache__
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ directories
            if "__pycache__" in py_file.parts:
                continue
            python_files.append(py_file)

    return python_files


def _parse_black_output(stdout: str, working_dir: Optional[Path] = None) -> List[Path]:
    """Parse Black stdout to find files that were reformatted.

    Black outputs lines like:
    - "reformatted /path/to/file.py" (when actually reformatting)
    - "would reformat /path/to/file.py" (when using --check)

    Args:
        stdout: Black command stdout output
        working_dir: Working directory to resolve relative paths (optional)

    Returns:
        List of file paths that were reformatted
    """
    reformatted_files = []

    # Pattern to match reformatted files (both actual and "would reformat")
    pattern = r"(?:reformatted|would reformat)\s+(.+\.py)"

    for line in stdout.splitlines():
        match = re.search(pattern, line.strip())
        if match:
            file_path_str = match.group(1)
            file_path = Path(file_path_str)

            # If path is relative and we have a working directory, make it absolute
            if not file_path.is_absolute() and working_dir:
                file_path = working_dir / file_path

            reformatted_files.append(file_path)

    return reformatted_files


def _build_black_command(config: FormatterConfig) -> List[str]:
    """Build Black command with configuration options.

    Args:
        config: FormatterConfig with Black settings

    Returns:
        Complete command as list of strings
    """
    command = ["black"]

    # Add line-length option
    if "line-length" in config.settings:
        command.extend(["--line-length", str(config.settings["line-length"])])

    # Add target-version options (can be multiple)
    if "target-version" in config.settings:
        target_versions = config.settings["target-version"]
        if isinstance(target_versions, list):
            for version in target_versions:
                command.extend(["--target-version", version])
        else:
            command.extend(["--target-version", target_versions])

    # Add target directories as arguments
    for directory in config.target_directories:
        command.append(str(directory))

    return command
