#!/usr/bin/env python3
"""Tests for git utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.utils.git_utils import get_branch_name_for_logging


class TestGetBranchNameForLogging:
    """Tests for get_branch_name_for_logging function."""

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_returns_branch_name_when_available(
        self, mock_get_branch: MagicMock
    ) -> None:
        """Test that branch name is returned when git repo is available."""
        mock_get_branch.return_value = "fix/improve-logging"

        result = get_branch_name_for_logging(project_dir="/some/path")

        assert result == "fix/improve-logging"
        mock_get_branch.assert_called_once()

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_returns_none_for_detached_head(self, mock_get_branch: MagicMock) -> None:
        """Test that None is returned for detached HEAD state."""
        mock_get_branch.return_value = "HEAD"

        result = get_branch_name_for_logging(project_dir="/some/path")

        assert result is None

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_falls_back_to_issue_id_when_branch_unavailable(
        self, mock_get_branch: MagicMock
    ) -> None:
        """Test fallback to issue_id format when branch unavailable."""
        mock_get_branch.return_value = None

        result = get_branch_name_for_logging(project_dir="/some/path", issue_id=123)

        assert result == "123-issue"

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_falls_back_to_issue_id_when_detached_head(
        self, mock_get_branch: MagicMock
    ) -> None:
        """Test fallback to issue_id format when in detached HEAD."""
        mock_get_branch.return_value = "HEAD"

        result = get_branch_name_for_logging(project_dir="/some/path", issue_id="456")

        assert result == "456-issue"

    def test_returns_issue_id_format_when_no_project_dir(self) -> None:
        """Test that issue_id format is returned when no project_dir provided."""
        result = get_branch_name_for_logging(issue_id=789)

        assert result == "789-issue"

    def test_returns_none_when_no_context(self) -> None:
        """Test that None is returned when no context available."""
        result = get_branch_name_for_logging()

        assert result is None

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_handles_exception_gracefully(self, mock_get_branch: MagicMock) -> None:
        """Test that exceptions are handled gracefully."""
        mock_get_branch.side_effect = Exception("Git error")

        # Should not raise, should fall back to issue_id
        result = get_branch_name_for_logging(project_dir="/some/path", issue_id=123)

        assert result == "123-issue"

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_handles_exception_returns_none_without_fallback(
        self, mock_get_branch: MagicMock
    ) -> None:
        """Test that exceptions return None when no fallback available."""
        mock_get_branch.side_effect = Exception("Git error")

        result = get_branch_name_for_logging(project_dir="/some/path")

        assert result is None

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_accepts_path_object(self, mock_get_branch: MagicMock) -> None:
        """Test that Path objects are accepted for project_dir."""
        mock_get_branch.return_value = "main"

        result = get_branch_name_for_logging(project_dir=Path("/some/path"))

        assert result == "main"
        mock_get_branch.assert_called_once()

    @patch("mcp_coder.utils.git_utils.get_current_branch_name")
    def test_prefers_branch_over_issue_id(self, mock_get_branch: MagicMock) -> None:
        """Test that actual branch name is preferred over issue_id fallback."""
        mock_get_branch.return_value = "feature/my-feature"

        result = get_branch_name_for_logging(project_dir="/some/path", issue_id=123)

        assert result == "feature/my-feature"

    def test_issue_id_handles_string_input(self) -> None:
        """Test that string issue_id is handled correctly."""
        result = get_branch_name_for_logging(issue_id="ABC-123")

        assert result == "ABC-123-issue"

    def test_issue_id_handles_int_input(self) -> None:
        """Test that int issue_id is handled correctly."""
        result = get_branch_name_for_logging(issue_id=42)

        assert result == "42-issue"
