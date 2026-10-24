"""Tests for create_pr workflow helper functions."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import ClosingPRRef
from mcp_coder.workflows.create_pr.core import (
    _add_pr_assignee_best_effort,
    _cleanup_commit_push,
    _resolve_issue_from_pr,
    validate_branch_issue_linkage,
)

CORE = "mcp_coder.workflows.create_pr.core"


class TestCleanupCommitPush:
    """Test suite for _cleanup_commit_push helper."""

    @patch(f"{CORE}.git_push")
    @patch(f"{CORE}.commit_all_changes")
    @patch(f"{CORE}.is_working_directory_clean")
    @patch(f"{CORE}.cleanup_repository")
    def test_success_returns_none(
        self,
        mock_cleanup: MagicMock,
        mock_clean: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Cleanup, commit and push all succeed → None."""
        mock_cleanup.return_value = True
        mock_clean.return_value = False
        mock_commit.return_value = {"success": True, "commit_hash": "abc"}
        mock_push.return_value = {"success": True}

        assert _cleanup_commit_push(Path("/test")) is None
        mock_commit.assert_called_once()
        mock_push.assert_called_once_with(Path("/test"))

    @patch(f"{CORE}.git_push")
    @patch(f"{CORE}.commit_all_changes")
    @patch(f"{CORE}.is_working_directory_clean")
    @patch(f"{CORE}.cleanup_repository")
    def test_cleanup_failure(
        self,
        mock_cleanup: MagicMock,
        mock_clean: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """cleanup_repository False → ("cleanup", ...), nothing pushed."""
        mock_cleanup.return_value = False

        assert _cleanup_commit_push(Path("/test")) == (
            "cleanup",
            "Repository cleanup failed",
        )
        mock_clean.assert_not_called()
        mock_commit.assert_not_called()
        mock_push.assert_not_called()

    @patch(f"{CORE}.git_push")
    @patch(f"{CORE}.commit_all_changes")
    @patch(f"{CORE}.is_working_directory_clean")
    @patch(f"{CORE}.cleanup_repository")
    def test_commit_error(
        self,
        mock_cleanup: MagicMock,
        mock_clean: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Commit fails with a real error → ("cleanup", ...), nothing pushed."""
        mock_cleanup.return_value = True
        mock_clean.return_value = False
        mock_commit.return_value = {"success": False, "error": "disk full"}

        assert _cleanup_commit_push(Path("/test")) == (
            "cleanup",
            "Failed to commit cleanup: disk full",
        )
        mock_push.assert_not_called()

    @patch(f"{CORE}.git_push")
    @patch(f"{CORE}.commit_all_changes")
    @patch(f"{CORE}.is_working_directory_clean")
    @patch(f"{CORE}.cleanup_repository")
    def test_commit_no_staged_files_continues(
        self,
        mock_cleanup: MagicMock,
        mock_clean: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Commit reports "No staged files" → continues to push."""
        mock_cleanup.return_value = True
        mock_clean.return_value = False
        mock_commit.return_value = {"success": False, "error": "No staged files"}
        mock_push.return_value = {"success": True}

        assert _cleanup_commit_push(Path("/test")) is None
        mock_push.assert_called_once()

    @patch(f"{CORE}.git_push")
    @patch(f"{CORE}.commit_all_changes")
    @patch(f"{CORE}.is_working_directory_clean")
    @patch(f"{CORE}.cleanup_repository")
    def test_push_failure(
        self,
        mock_cleanup: MagicMock,
        mock_clean: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Push fails → ("push", <error>)."""
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_push.return_value = {"success": False, "error": "rejected"}

        assert _cleanup_commit_push(Path("/test")) == ("push", "rejected")

    @patch(f"{CORE}.git_push")
    @patch(f"{CORE}.commit_all_changes")
    @patch(f"{CORE}.is_working_directory_clean")
    @patch(f"{CORE}.cleanup_repository")
    def test_clean_tree_skips_commit(
        self,
        mock_cleanup: MagicMock,
        mock_clean: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Clean working tree → no commit call, still pushes."""
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_push.return_value = {"success": True}

        assert _cleanup_commit_push(Path("/test")) is None
        mock_commit.assert_not_called()
        mock_push.assert_called_once()


class TestResolveIssueFromPr:
    """Test suite for _resolve_issue_from_pr helper."""

    @patch(f"{CORE}.PullRequestManager")
    def test_single_closing_issue(self, mock_pr_manager_class: MagicMock) -> None:
        """[7] → 7."""
        mock_pr_manager_class.return_value.get_closing_issue_numbers.return_value = [7]

        assert _resolve_issue_from_pr(Path("/test"), 42) == 7
        mock_pr_manager_class.return_value.get_closing_issue_numbers.assert_called_once_with(
            42
        )

    @patch(f"{CORE}.PullRequestManager")
    def test_multiple_closing_issues_uses_first(
        self, mock_pr_manager_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """[7, 8] → 7 and a warning."""
        mock_pr_manager_class.return_value.get_closing_issue_numbers.return_value = [
            7,
            8,
        ]

        with caplog.at_level(logging.WARNING):
            assert _resolve_issue_from_pr(Path("/test"), 42) == 7

        assert any(r.levelno == logging.WARNING for r in caplog.records)

    @patch(f"{CORE}.PullRequestManager")
    def test_no_closing_issues(self, mock_pr_manager_class: MagicMock) -> None:
        """[] → None."""
        mock_pr_manager_class.return_value.get_closing_issue_numbers.return_value = []

        assert _resolve_issue_from_pr(Path("/test"), 42) is None

    @patch(f"{CORE}.PullRequestManager")
    def test_exception_returns_none(
        self, mock_pr_manager_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Lookup raises → None and a warning, never re-raises."""
        mock_pr_manager_class.return_value.get_closing_issue_numbers.side_effect = (
            RuntimeError("boom")
        )

        with caplog.at_level(logging.WARNING):
            assert _resolve_issue_from_pr(Path("/test"), 42) is None

        assert "non-blocking" in caplog.text


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
        mock_manager.get_linked_branch_and_closing_prs_or_none.return_value = (
            ["123-feature"],
            [],
        )

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns 123
        assert result == 123
        mock_get_branch.assert_called_once_with(tmp_path)
        mock_manager_class.assert_called_once_with(project_dir=tmp_path)
        mock_manager.get_linked_branch_and_closing_prs_or_none.assert_called_once_with(
            123
        )

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
        mock_manager.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)
        mock_manager_class.assert_called_once_with(project_dir=tmp_path)
        mock_manager.get_linked_branch_and_closing_prs_or_none.assert_called_once_with(
            123
        )

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.IssueBranchManager")
    def test_validate_branch_issue_linkage_post_pr_closing_pr(
        self, mock_manager_class: MagicMock, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation succeeds via an open closing PR once a PR exists."""
        mock_get_branch.return_value = "123-feature"
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_linked_branch_and_closing_prs_or_none.return_value = (
            [],
            [ClosingPRRef(42, "123-feature")],
        )

        result = validate_branch_issue_linkage(tmp_path)

        assert result == 123

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.IssueBranchManager")
    def test_validate_branch_issue_linkage_lookup_failed(
        self,
        mock_manager_class: MagicMock,
        mock_get_branch: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests validation returns None and logs an ERROR when lookup fails."""
        mock_get_branch.return_value = "123-feature"
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_linked_branch_and_closing_prs_or_none.return_value = None

        with caplog.at_level(logging.ERROR):
            result = validate_branch_issue_linkage(tmp_path)

        assert result is None
        assert any(record.levelno == logging.ERROR for record in caplog.records)

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
