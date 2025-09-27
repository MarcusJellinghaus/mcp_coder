"""
Thin wrapper for mcp_code_checker library.

Provides a simplified interface to mcp_code_checker's mypy functionality.
"""

from pathlib import Path
from typing import Union

from mcp_code_checker.code_checker_mypy import MypyResult, run_mypy_check as _run_mypy_check


def run_mypy_check(project_dir: Union[str, Path]) -> MypyResult:
    """
    Run mypy type checking on the project.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        MypyResult from mcp_code_checker with return_code, messages, errors_found, etc.
    """
    return _run_mypy_check(
        project_dir=str(project_dir),
        strict=True,
        disable_error_codes=None,
        target_directories=None,  # Let MCP tool choose defaults (src/, tests/)
        follow_imports="normal",
        cache_dir=None
    )


def has_mypy_errors(project_dir: Union[str, Path]) -> bool:
    """
    Quick check if project has mypy type errors.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        True if there are mypy errors, False if clean
    """
    result = run_mypy_check(project_dir)
    return (result.errors_found or 0) > 0