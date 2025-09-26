"""
Wrapper module for mcp_code_checker library.

This module provides a clean interface to the external mcp_code_checker library,
handling imports, error conditions, and result interpretation in a consistent way.
"""

from pathlib import Path
from typing import Optional, Union


class MypyCheckResult:
    """Result object for mypy type checking operations."""
    
    def __init__(self, has_errors: bool, output: str, error_count: int = 0):
        self.has_errors = has_errors
        self.output = output
        self.error_count = error_count
    
    def __bool__(self) -> bool:
        """Return True if there are NO errors (for easy checking)."""
        return not self.has_errors


def run_mypy_check(project_dir: Union[str, Path]) -> MypyCheckResult:
    """
    Run mypy type checking on the project using mcp_code_checker.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        MypyCheckResult with has_errors, output, and error_count
        
    Raises:
        ImportError: If mcp_code_checker is not available
        Exception: If mypy check fails to run
    """
    try:
        from mcp_code_checker.code_checker_mypy import run_mypy_check as _run_mypy
    except ImportError as e:
        raise ImportError(f"mcp_code_checker is required but not available: {e}")
    
    try:
        # Use the API with default settings
        result = _run_mypy(
            project_dir=str(project_dir),
            strict=True,
            disable_error_codes=None,
            target_directories=None,  # Let MCP tool choose defaults (src/, tests/)
            follow_imports="normal",
            cache_dir=None
        )
        
        # Handle different result types from the external library
        if result is None:
            return MypyCheckResult(has_errors=False, output="", error_count=0)
        
        # Convert result to string regardless of type
        if isinstance(result, str):
            result_str = result.strip()
        else:
            result_str = str(result).strip()
        
        # Check for success patterns
        success_patterns = [
            "No type errors found",
            "check completed",
            "no issues found"
        ]
        
        is_success = (
            not result_str or
            any(pattern in result_str for pattern in success_patterns) or
            any(pattern in result_str.lower() for pattern in ["check completed", "no issues found"])
        )
        
        if is_success:
            return MypyCheckResult(has_errors=False, output=result_str, error_count=0)
        
        # Count error lines (rough estimate)
        error_lines = [line for line in result_str.split('\n') if 'error:' in line.lower()]
        return MypyCheckResult(has_errors=True, output=result_str, error_count=len(error_lines))
            
    except Exception as e:
        raise Exception(f"Failed to run mypy check via mcp_code_checker: {e}")


def has_mypy_errors(project_dir: Union[str, Path]) -> bool:
    """
    Quick check if project has mypy type errors.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        True if there are mypy errors, False if clean
        
    Raises:
        ImportError: If mcp_code_checker is not available
        Exception: If mypy check fails to run
    """
    result = run_mypy_check(project_dir)
    return result.has_errors