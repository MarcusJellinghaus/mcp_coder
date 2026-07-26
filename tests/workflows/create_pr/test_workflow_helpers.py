"""Tests for create_pr workflow helper functions."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import (
    _add_pr_assignee_best_effort,
    validate_branch_issue_linkage,
)


class TestAddPrAssigneeBestEffort:
    """Test suite for _add_pr_assignee_best_effort helper."""

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_authenticated_username")
    @patch("mcp_coder.workflows.create_pr.core.get_repo_flag")
    def test_flag_on_assigns_pr_to_authenticated_user(
        self,
        mock_get_flag: MagicMock,
        mock_get_username: MagicMock,
        mock_pr_manager_class: MagicMock,
    ) -> None:
        """Flag on → add_assignees called once with the PR number + username."""
        mock_get_flag.return_value = True
        mock_get_username.return_value = "octocat"
        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr

        _add_pr_assignee_best_effort(Path("/test"), 42)

        mock_get_flag.assert_called_once_with(
            Path("/test"), "auto_review_implementation"
        )
        mock_pr_manager_class.assert_called_once_with(Path("/test"))
        mock_pr_mgr.add_assignees.assert_called_once_with(42, "octocat")

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_authenticated_username")
    @patch("mcp_coder.workflows.create_pr.core.get_repo_flag")
    def test_flag_off_skips_assignment(
        self,
        mock_get_flag: MagicMock,
        mock_get_username: MagicMock,
        mock_pr_manager_class: MagicMock,
    ) -> None:
        """Flag off → add_assignees never called (manual PRs don't get assigned)."""
        mock_get_flag.return_value = False

        _add_pr_assignee_best_effort(Path("/test"), 42)

        mock_get_username.assert_not_called()
        mock_pr_manager_class.assert_not_called()

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_authenticated_username")
    @patch("mcp_coder.workflows.create_pr.core.get_repo_flag")
    def test_assignee_add_failure_is_swallowed(
        self,
        mock_get_flag: MagicMock,
        mock_get_username: MagicMock,
        mock_pr_manager_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """add_assignees raises → helper logs a warning and never re-raises."""
        mock_get_flag.return_value = True
        mock_get_username.return_value = "octocat"
        mock_pr_mgr = MagicMock()
        mock_pr_mgr.add_assignees.side_effect = RuntimeError("boom")
        mock_pr_manager_class.return_value = mock_pr_mgr

        with caplog.at_level(logging.WARNING):
            # Must not raise.
            _add_pr_assignee_best_effort(Path("/test"), 42)

        assert "non-blocking" in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_authenticated_username")
    @patch("mcp_coder.workflows.create_pr.core.get_repo_flag")
    def test_auth_failure_is_swallowed(
        self,
        mock_get_flag: MagicMock,
        mock_get_username: MagicMock,
        mock_pr_manager_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_authenticated_username raising ValueError is caught (no re-raise)."""
        mock_get_flag.return_value = True
        mock_get_username.side_effect = ValueError("no token")

        with caplog.at_level(logging.WARNING):
            _add_pr_assignee_best_effort(Path("/test"), 42)

        mock_pr_manager_class.assert_not_called()
        assert "non-blocking" in caplog.text


class TestValidateBranchIssueLinkage:
    """Test suite for validate_branch_issue_linkage helper function."""

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.IssueBranchManager")
    def test_validate_branch_issue_linkage_success(
        self, mock_manager_class: MagicMock, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests successful validation when branch is linked to issue."""
        # Setup: Mock branch name "123-feature", linked branches ["123-feature"]
        mock_get_branch.return_value = "123-feature"
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_linked_branches.return_value = ["123-feature"]

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns 123
        assert result == 123
        mock_get_branch.assert_called_once_with(tmp_path)
        mock_manager_class.assert_called_once_with(project_dir=tmp_path)
        mock_manager.get_linked_branches.assert_called_once_with(123)

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.IssueBranchManager")
    def test_validate_branch_issue_linkage_not_linked(
        self, mock_manager_class: MagicMock, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation fails when branch is not linked."""
        # Setup: Mock branch name "123-feature", linked branches []
        mock_get_branch.return_value = "123-feature"
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_linked_branches.return_value = []

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)
        mock_manager_class.assert_called_once_with(project_dir=tmp_path)
        mock_manager.get_linked_branches.assert_called_once_with(123)

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    def test_validate_branch_issue_linkage_no_issue_number(
        self, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation fails when branch name has no issue number."""
        # Setup: Mock branch name "feature-branch" (no issue number prefix)
        mock_get_branch.return_value = "feature-branch"

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    def test_validate_branch_issue_linkage_no_branch_name(
        self, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation fails when branch name cannot be determined."""
        # Setup: Mock branch name return None
        mock_get_branch.return_value = None

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)
