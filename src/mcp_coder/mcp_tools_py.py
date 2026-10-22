"""Thin wrapper for mcp_tools_py library.

Provides a simplified interface to mcp_tools_py's mypy, pytest, pylint and
formatter functionality.
"""

import sys
from pathlib import Path
from typing import Any

from mcp_tools_py.code_checker_mypy import MypyResult
from mcp_tools_py.code_checker_mypy import run_mypy_check as _run_mypy_check
from mcp_tools_py.code_checker_pylint import PylintResult
from mcp_tools_py.code_checker_pylint import get_pylint_results as _get_pylint_results
from mcp_tools_py.code_checker_pytest import (
    check_code_with_pytest as _check_code_with_pytest,
)
from mcp_tools_py.formatter.models import FormatterResult
from mcp_tools_py.formatter.runner import resolve_steps
from mcp_tools_py.formatter.runner import run_format_code as _run_format_code

__all__ = [
    "FormatterResult",
    "MypyResult",
    "PylintResult",
    "has_mypy_errors",
    "resolve_steps",
    "run_format_code",
    "run_mypy_check",
    "run_pylint_check",
    "run_pytest_check",
]


def run_format_code(
    project_dir: str | Path,
) -> dict[str, FormatterResult]:
    """Run the project's configured formatter.

    Args:
        project_dir: Path to the project directory.

    Returns:
        Dict mapping formatter step name to FormatterResult, in execution order.

    Raises:
        RuntimeError: If target directory resolution fails.
        ValueError: If no formatter can be resolved (from resolve_steps).
    """  # noqa: DOC502 - ValueError propagated from resolve_steps.
    from mcp_tools_py.utils.project_config import resolve_target_directories

    project_root = Path(str(project_dir))
    target_dirs = resolve_target_directories(str(project_root), None)
    if isinstance(target_dirs, str):
        raise RuntimeError(target_dirs)

    return _run_format_code(sys.executable, project_root, target_dirs, steps=None)


def run_pytest_check(project_dir: str | Path) -> dict[str, Any]:
    """Run pytest with project defaults (no marker filter, library timeouts).

    Args:
        project_dir: Path to the project directory.

    Returns:
        Result dict from mcp_tools_py, unchanged. On a completed run it
        contains success, summary, summary_text, failed_tests_prompt,
        test_results (a PytestReport) and error_info (non-None for any
        non-zero pytest exit, including ordinary test failures). On a crash
        (timeout, internal error, missing report) it contains only
        success=False and error.
    """
    return _check_code_with_pytest(
        project_dir=str(project_dir),
        python_executable=sys.executable,
    )


def run_pylint_check(project_dir: str | Path) -> PylintResult:
    """Run pylint on the project's resolved target directories.

    Args:
        project_dir: Path to the project directory.

    Returns:
        PylintResult from mcp_tools_py with return_code, messages, error,
        raw_output.

    Raises:
        RuntimeError: If target directory resolution fails.
    """
    from mcp_tools_py.utils.project_config import resolve_target_directories

    project_root = Path(str(project_dir))
    target_dirs = resolve_target_directories(str(project_root), None)
    if isinstance(target_dirs, str):
        raise RuntimeError(target_dirs)

    return _get_pylint_results(
        project_dir=str(project_root),
        python_executable=sys.executable,
        target_directories=target_dirs,
    )


def run_mypy_check(
    project_dir: str | Path,
    target_directories: list[str] | None = None,
) -> MypyResult:
    """Run mypy type checking on the project.

    Args:
        project_dir: Path to the project directory
        target_directories: Optional list of directories to check relative to project_dir.
                          Defaults to ["src"] and conditionally "tests" if it exists.

    Returns:
        MypyResult from mcp_tools_py with return_code, messages, errors_found, etc.
    """
    return _run_mypy_check(
        project_dir=str(project_dir),
        python_executable=sys.executable,
        disable_error_codes=None,
        target_directories=target_directories,
        follow_imports="normal",
        cache_dir=None,
    )


def has_mypy_errors(project_dir: str | Path) -> bool:
    """Quick check if project has mypy type errors.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if there are mypy errors, False if clean
    """
    result = run_mypy_check(project_dir)
    return (result.errors_found or 0) > 0
