"""Black formatter implementation with exit code change detection.

Based on Step 0 analysis findings, this module implements Black formatting using:
- Two-phase approach (check first, format if needed)
- Exit code change detection (0=no changes, 1=changes needed)
- Shared configuration reading using utility patterns
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_coder.utils.subprocess_runner import execute_command

from .models import FormatterResult
from .utils import find_python_files, get_default_target_dirs, read_tool_config


def format_with_black(
    project_root: Path, target_dirs: Optional[List[str]] = None
) -> FormatterResult:
    """Format code using proven Black CLI patterns with exit code detection.

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

        # Track files that were changed
        files_changed = []

        # Process each target directory
        for target_dir in target_dirs:
            target_path = project_root / target_dir
            if not target_path.exists():
                continue

            # Find Python files to process
            python_files = find_python_files(target_path)

            for file_path in python_files:
                # Check if formatting is needed
                if _check_black_changes(str(file_path), config):
                    # Apply formatting
                    if _apply_black_formatting(str(file_path), config):
                        files_changed.append(str(file_path))
                    else:
                        # Formatting failed
                        return FormatterResult(
                            success=False,
                            files_changed=[],
                            formatter_name="black",
                            error_message=f"Failed to format {file_path}",
                        )

        return FormatterResult(
            success=True,
            files_changed=files_changed,
            formatter_name="black",
            error_message=None,
        )

    except Exception as e:
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


def _check_black_changes(file_path: str, config: Dict[str, Any]) -> bool:
    """Check if Black formatting needed using --check (exit code pattern).

    Args:
        file_path: Path to the Python file to check
        config: Black configuration dictionary

    Returns:
        True if formatting is needed, False if already formatted

    Raises:
        Exception: If Black check command fails with syntax errors
    """
    # Build Black check command
    command = ["black", "--check", file_path]

    # Add configuration options
    command.extend(["--line-length", str(config["line-length"])])
    for target_version in config["target-version"]:
        command.extend(["--target-version", target_version])

    # Execute Black check
    result = execute_command(command)

    if result.return_code == 0:
        # No changes needed
        return False
    elif result.return_code == 1:
        # Changes needed
        return True
    else:
        # Syntax error or other failure (exit code 123+)
        raise Exception(f"Black check failed: {result.stderr}")


def _apply_black_formatting(file_path: str, config: Dict[str, Any]) -> bool:
    """Apply Black formatting and return success status.

    Args:
        file_path: Path to the Python file to format
        config: Black configuration dictionary

    Returns:
        True if formatting succeeded, False otherwise
    """
    # Build Black format command
    command = ["black", file_path]

    # Add configuration options
    command.extend(["--line-length", str(config["line-length"])])
    for target_version in config["target-version"]:
        command.extend(["--target-version", target_version])

    # Execute Black formatting
    result = execute_command(command)

    # Return success status (exit 0 = success, exit 1 = changes applied, both are success)
    return result.return_code in (0, 1)
