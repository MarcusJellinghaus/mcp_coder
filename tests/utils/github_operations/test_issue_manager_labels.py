"""Unit tests for IssueManager label operations with mocked dependencies."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest
from github.GithubException import GithubException

from mcp_coder.utils.github_operations.issues import IssueManager
from mcp_coder.utils.github_operations.issues.base import (
    validate_comment_id,
    validate_issue_number,
)


@pytest.mark.git_integration
class TestIssueManagerLabels:
    """Unit tests for IssueManager label operations with mocked dependencies."""

    def test_add_labels_success(self, mock_issue_manager: IssueManager) -> None:
        """Test successful label addition."""
        issue_number = 1
        labels = ["bug", "enhancement"]
        mock_issue = MagicMock()
        mock_issue.number = issue_number

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.add_labels(issue_number, *labels)

        mock_issue.add_to_labels.assert_called_once_with(*labels)

    def test_add_labels_single_label(self, mock_issue_manager: IssueManager) -> None:
        """Test adding a single label."""
        issue_number = 1
        labels = ["bug"]
        mock_issue = MagicMock()

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.add_labels(issue_number, *labels)

        mock_issue.add_to_labels.assert_called_once_with(*labels)

    def test_add_labels_invalid_issue_number(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test adding labels with invalid issue number."""
        with pytest.raises(ValueError, match="Issue number must be a positive integer"):
            mock_issue_manager.add_labels(0, "bug")

    def test_add_labels_no_labels_provided(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test that empty labels list raises ValueError."""
        with pytest.raises(ValueError, match="At least one label must be provided"):
            mock_issue_manager.add_labels(1)

    def test_add_labels_auth_error_raises(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test that authentication errors are raised when adding labels."""
        mock_issue_manager._repository.get_issue.side_effect = GithubException(
            401, {"message": "Bad credentials"}, None
        )

        with pytest.raises(GithubException):
            mock_issue_manager.add_labels(1, "bug")

    def test_remove_labels_success(self, mock_issue_manager: IssueManager) -> None:
        """Test successful label removal."""
        issue_number = 1
        labels = ["bug", "enhancement"]
        mock_issue = MagicMock()
        mock_issue.number = issue_number

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.remove_labels(issue_number, *labels)

        mock_issue.remove_from_labels.assert_called_once_with(*labels)

    def test_remove_labels_single_label(self, mock_issue_manager: IssueManager) -> None:
        """Test removing a single label."""
        issue_number = 1
        labels = ["bug"]
        mock_issue = MagicMock()

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.remove_labels(issue_number, *labels)

        mock_issue.remove_from_labels.assert_called_once_with(*labels)

    def test_remove_labels_invalid_issue_number(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test removing labels with invalid issue number."""
        with pytest.raises(ValueError, match="Issue number must be a positive integer"):
            mock_issue_manager.remove_labels(0, "bug")

    def test_remove_labels_no_labels_provided(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test that empty labels list raises ValueError."""
        with pytest.raises(ValueError, match="At least one label must be provided"):
            mock_issue_manager.remove_labels(1)

    def test_remove_labels_auth_error_raises(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test that authentication errors are raised when removing labels."""
        mock_issue_manager._repository.get_issue.side_effect = GithubException(
            401, {"message": "Bad credentials"}, None
        )

        with pytest.raises(GithubException):
            mock_issue_manager.remove_labels(1, "bug")

    def test_set_labels_success(self, mock_issue_manager: IssueManager) -> None:
        """Test successful label setting."""
        issue_number = 1
        labels = ["bug", "priority-high"]
        mock_issue = MagicMock()
        mock_issue.number = issue_number

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.set_labels(issue_number, *labels)

        mock_issue.set_labels.assert_called_once_with(*labels)

    def test_set_labels_empty_to_clear_all(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test setting empty labels to clear all labels."""
        issue_number = 1
        mock_issue = MagicMock()

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.set_labels(issue_number)

        mock_issue.set_labels.assert_called_once_with()

    def test_set_labels_single_label(self, mock_issue_manager: IssueManager) -> None:
        """Test setting a single label."""
        issue_number = 1
        labels = ["bug"]
        mock_issue = MagicMock()

        mock_issue_manager._repository.get_issue.return_value = mock_issue

        mock_issue_manager.set_labels(issue_number, *labels)

        mock_issue.set_labels.assert_called_once_with(*labels)

    def test_set_labels_invalid_issue_number(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test setting labels with invalid issue number."""
        with pytest.raises(ValueError, match="Issue number must be a positive integer"):
            mock_issue_manager.set_labels(0, "bug")

    def test_set_labels_auth_error_raises(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Test that authentication errors are raised when setting labels."""
        mock_issue_manager._repository.get_issue.side_effect = GithubException(
            401, {"message": "Bad credentials"}, None
        )

        with pytest.raises(GithubException):
            mock_issue_manager.set_labels(1, "bug")
