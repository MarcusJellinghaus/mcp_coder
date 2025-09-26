"""
Tests for workflows/implement.py module.

These tests verify key functions in the implement workflow script,
focusing on utility functions that can be tested in isolation.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import functions from the implement module
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "workflows"))

from implement import (
    check_prerequisites,
    has_implementation_tasks,
    resolve_project_dir,
    _run_mypy_check,
)


class TestCheckPrerequisites:
    """Test the check_prerequisites function."""

    def test_check_prerequisites_with_valid_git_repo(self):
        """Test prerequisites check with a valid git repository."""
        # Use current project directory which should be a valid git repo
        project_dir = Path.cwd()

        # Should pass for current project
        result = check_prerequisites(project_dir)
        assert isinstance(result, bool)
        # Current project should have .git and pr_info/TASK_TRACKER.md
        assert result is True

    def test_check_prerequisites_with_non_git_directory(self):
        """Test prerequisites check with non-git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Should fail - no .git directory
            result = check_prerequisites(temp_path)
            assert result is False


class TestHasImplementationTasks:
    """Test the has_implementation_tasks function."""

    def test_has_implementation_tasks_current_project(self):
        """Test has_implementation_tasks on current project."""
        project_dir = Path.cwd()

        # Should not crash and return a boolean
        result = has_implementation_tasks(project_dir)
        assert isinstance(result, bool)
        # Current project may or may not have implementation tasks
        # Just verify it returns a consistent boolean

    def test_has_implementation_tasks_with_invalid_directory(self):
        """Test has_implementation_tasks with invalid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_dir = Path(temp_dir) / "nonexistent"

            # Should handle gracefully and return False
            result = has_implementation_tasks(invalid_dir)
            assert result is False


class TestResolveProjectDir:
    """Test the resolve_project_dir function."""

    def test_resolve_project_dir_with_none(self):
        """Test resolve_project_dir with None argument."""
        # Should use current directory
        result = resolve_project_dir(None)
        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result == Path.cwd().resolve()

    def test_resolve_project_dir_with_current_directory(self):
        """Test resolve_project_dir with current directory."""
        current_dir = str(Path.cwd())
        result = resolve_project_dir(current_dir)

        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result == Path.cwd().resolve()

    def test_resolve_project_dir_with_nonexistent_directory(self):
        """Test resolve_project_dir with non-existent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_path = str(Path(temp_dir) / "nonexistent")

            # Should exit with error for non-existent directory
            with pytest.raises(SystemExit):
                resolve_project_dir(nonexistent_path)


class TestRunMypyCheck:
    """Test the _run_mypy_check function using our wrapper."""

    def test_run_mypy_check_integration(self):
        """Test _run_mypy_check function integration."""
        project_dir = Path.cwd()

        # Should not crash and return proper type
        result = _run_mypy_check(project_dir)

        # Result should be None (no errors) or string (error output)
        assert result is None or isinstance(result, str)

    @patch("mcp_coder.mcp_code_checker.run_mypy_check")
    def test_run_mypy_check_with_no_errors(self, mock_run_mypy):
        """Test _run_mypy_check when wrapper returns no errors."""
        from mcp_coder.mcp_code_checker import MypyCheckResult

        # Mock the wrapper to return no errors
        mock_result = MypyCheckResult(
            has_errors=False, output="No issues found", error_count=0
        )
        mock_run_mypy.return_value = mock_result

        project_dir = Path.cwd()
        result = _run_mypy_check(project_dir)

        # Should return None for no errors
        assert result is None
        mock_run_mypy.assert_called_once_with(project_dir)

    @patch("mcp_coder.mcp_code_checker.run_mypy_check")
    def test_run_mypy_check_with_errors(self, mock_run_mypy):
        """Test _run_mypy_check when wrapper returns errors."""
        from mcp_coder.mcp_code_checker import MypyCheckResult

        # Mock the wrapper to return errors
        error_output = "file.py:10: error: Missing type annotation"
        mock_result = MypyCheckResult(
            has_errors=True, output=error_output, error_count=1
        )
        mock_run_mypy.return_value = mock_result

        project_dir = Path.cwd()
        result = _run_mypy_check(project_dir)

        # Should return the error output
        assert result == error_output
        mock_run_mypy.assert_called_once_with(project_dir)

    @patch("mcp_coder.mcp_code_checker.run_mypy_check")
    def test_run_mypy_check_import_error(self, mock_run_mypy):
        """Test _run_mypy_check when import fails."""
        # Mock import error
        mock_run_mypy.side_effect = ImportError("mcp_coder.mcp_code_checker not found")

        project_dir = Path.cwd()

        # Should raise Exception with appropriate message
        with pytest.raises(Exception) as exc_info:
            _run_mypy_check(project_dir)

        assert "mcp_coder.mcp_code_checker is required but not available" in str(
            exc_info.value
        )


class TestWorkflowIntegration:
    """Integration tests for workflow components."""

    def test_workflow_dependencies_available(self):
        """Test that all required dependencies are available."""
        # Test that key imports work
        from implement import (
            get_prompt,
            ask_llm,
            generate_commit_message_with_llm,
            format_code,
            commit_all_changes,
            get_incomplete_tasks,
        )

        # All imports should succeed without error
        assert get_prompt is not None
        assert ask_llm is not None
        assert generate_commit_message_with_llm is not None
        assert format_code is not None
        assert commit_all_changes is not None
        assert get_incomplete_tasks is not None
