"""Tests for shared workflow_steps prerequisite steps."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from mcp_coder.workflow_steps.prerequisites import check_git_clean


class TestCheckGitClean:
    """Test the shared check_git_clean step."""

    @patch("mcp_coder.workflow_steps.prerequisites.is_working_directory_clean")
    def test_git_clean_success(self, mock_is_clean: MagicMock) -> None:
        """Test git clean check when working directory is clean."""
        mock_is_clean.return_value = True

        result = check_git_clean(Path("/test/project"))

        assert result is True
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )

    @patch("mcp_coder.workflow_steps.prerequisites.is_working_directory_clean")
    def test_git_clean_dirty_directory(self, mock_is_clean: MagicMock) -> None:
        """Test git clean check when working directory is dirty."""
        mock_is_clean.return_value = False

        result = check_git_clean(Path("/test/project"))

        assert result is False
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )

    @patch("mcp_coder.workflow_steps.prerequisites.get_full_status")
    @patch("mcp_coder.workflow_steps.prerequisites.is_working_directory_clean")
    def test_git_clean_dirty_with_status_details(
        self, mock_is_clean: MagicMock, mock_get_status: MagicMock
    ) -> None:
        """Test git clean check logs detailed status when dirty."""
        mock_is_clean.return_value = False
        mock_get_status.return_value = {
            "staged": ["file1.py"],
            "modified": ["file2.py"],
            "untracked": ["file3.py"],
        }

        result = check_git_clean(Path("/test/project"))

        assert result is False
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )
        mock_get_status.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflow_steps.prerequisites.is_working_directory_clean")
    def test_git_clean_value_error(self, mock_is_clean: MagicMock) -> None:
        """Test git clean check handles ValueError from git operations."""
        mock_is_clean.side_effect = ValueError("Not a git repository")

        result = check_git_clean(Path("/test/project"))

        assert result is False
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )
