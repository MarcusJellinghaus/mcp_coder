"""Thin wrapper for mcp_tools_py library.

Provides a simplified interface to mcp_tools_py's mypy, pytest, pylint and
formatter functionality.
"""

import sys
from pathlib import Path
from typing import Any, Union

from mcp_tools_py.code_checker_mypy import MypyResult
from mcp_tools_py.code_checker_mypy import run_mypy_check as _run_mypy_check
from mcp_tools_py.code_checker_pylint import PylintResult
from mcp_tools_py.code_checker_pylint import get_pylint_results as _get_pylint_results
from mcp_tools_py.code_checker_pytest import (
    check_code_with_pytest as _check_code_with_pytest,
)
from mcp_tools_py.formatter.models import FormatterResult

__all__ = [
    "FormatterResult",
    "MypyResult",
    "PylintResult",
    "has_mypy_errors",
    "run_format_code",
    "run_mypy_check",
    "run_pylint_check",
    "run_pytest_check",
]


def run_format_code(
    project_dir: Union[str, Path],
) -> dict[str, FormatterResult]:
    """Run code formatters (isort, black) on the project.

    Args:
        project_dir: Path to the project directory.

    Returns:
        Dict mapping formatter step name to FormatterResult.

    Raises:
        RuntimeError: If target directory resolution fails.
    """
    from mcp_tools_py.formatter.black_runner import run_black
    from mcp_tools_py.formatter.isort_runner import run_isort
    from mcp_tools_py.utils.project_config import resolve_target_directories

    project_root = Path(str(project_dir))
    target_dirs = resolve_target_directories(str(project_root), None)
    if isinstance(target_dirs, str):
        raise RuntimeError(target_dirs)

    results: dict[str, FormatterResult] = {}
    for step_name, runner in [("isort", run_isort), ("black", run_black)]:
        result = runner(sys.executable, target_dirs, str(project_root))
        results[step_name] = result
        if not result.success:
            break
    return results


def run_pytest_check(project_dir: Union[str, Path]) -> dict[str, Any]:
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


def run_pylint_check(project_dir: Union[str, Path]) -> PylintResult:
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
    project_dir: Union[str, Path],
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
        strict=True,
        disable_error_codes=None,
        target_directories=target_directories,
        follow_imports="normal",
        cache_dir=None,
    )


def has_mypy_errors(project_dir: Union[str, Path]) -> bool:
    """Quick check if project has mypy type errors.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if there are mypy errors, False if clean
    """
    result = run_mypy_check(project_dir)
    return (result.errors_found or 0) > 0
