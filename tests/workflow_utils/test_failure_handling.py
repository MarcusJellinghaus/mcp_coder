"""Tests for shared workflow failure handling utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    format_elapsed_time,
    get_diff_stat,
    handle_workflow_failure,
)


class TestFormatElapsedTime:
    """Tests for format_elapsed_time."""

    def test_seconds_only(self) -> None:
        assert format_elapsed_time(45) == "45s"

    def test_minutes_and_seconds(self) -> None:
        assert format_elapsed_time(754) == "12m 34s"

    def test_hours_minutes_seconds(self) -> None:
        assert format_elapsed_time(3930) == "1h 5m 30s"

    def test_zero(self) -> None:
        assert format_elapsed_time(0) == "0s"


class TestGetDiffStat:
    """Tests for get_diff_stat."""

    @patch("mcp_coder.workflow_utils.failure_handling._safe_repo_context")
    def test_returns_diff_stat(self, mock_repo_ctx: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.git.diff.return_value = " file.py | 2 +-\n 1 file changed"
        mock_repo_ctx.return_value.__enter__ = MagicMock(return_value=mock_repo)
        mock_repo_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = get_diff_stat(Path("/fake/project"))

        assert result == " file.py | 2 +-\n 1 file changed"
        mock_repo.git.diff.assert_called_once_with("HEAD", "--stat")

    @patch("mcp_coder.workflow_utils.failure_handling._safe_repo_context")
    def test_returns_empty_on_error(self, mock_repo_ctx: MagicMock) -> None:
        mock_repo_ctx.return_value.__enter__ = MagicMock(
            side_effect=Exception("git error")
        )
        mock_repo_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = get_diff_stat(Path("/fake/project"))

        assert result == ""


class TestHandleWorkflowFailure:
    """Tests for handle_workflow_failure."""

    @pytest.fixture()
    def failure(self) -> WorkflowFailure:
        return WorkflowFailure(
            category="pr_creating_failed",
            stage="prerequisites",
            message="Something went wrong",
            elapsed_time=120.0,
        )

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_logs_failure_banner(
        self,
        _mock_extract: MagicMock,
        _mock_branch: MagicMock,
        _mock_issue_mgr: MagicMock,
        failure: WorkflowFailure,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _mock_branch.return_value = None
        with caplog.at_level("INFO"):
            handle_workflow_failure(
                failure=failure,
                comment_body="Test comment",
                project_dir=Path("/fake"),
                from_label_id="pr_creating",
            )

        assert "WORKFLOW FAILED" in caplog.text
        assert "pr_creating_failed" in caplog.text
        assert "prerequisites" in caplog.text
        assert "Something went wrong" in caplog.text

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_sets_label_when_update_labels_true(
        self,
        _mock_extract: MagicMock,
        _mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        _mock_branch.return_value = None
        mock_mgr = MagicMock()
        mock_issue_mgr_cls.return_value = mock_mgr

        handle_workflow_failure(
            failure=failure,
            comment_body="Test comment",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
            update_labels=True,
        )

        mock_mgr.update_workflow_label.assert_called_once_with(
            from_label_id="pr_creating",
            to_label_id="pr_creating_failed",
        )

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_skips_label_when_update_labels_false(
        self,
        _mock_extract: MagicMock,
        _mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        _mock_branch.return_value = None
        mock_mgr = MagicMock()
        mock_issue_mgr_cls.return_value = mock_mgr

        handle_workflow_failure(
            failure=failure,
            comment_body="Test comment",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
            update_labels=False,
        )

        mock_mgr.update_workflow_label.assert_not_called()

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_posts_comment_always(
        self,
        mock_extract: MagicMock,
        mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        """Comment is posted even when update_labels=False."""
        mock_branch.return_value = "42-feature"
        mock_extract.return_value = 42
        mock_mgr = MagicMock()
        mock_issue_mgr_cls.return_value = mock_mgr

        handle_workflow_failure(
            failure=failure,
            comment_body="Failure details here",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
            update_labels=False,
        )

        mock_mgr.add_comment.assert_called_once_with(42, "Failure details here")

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_posts_comment_with_provided_issue_number(
        self,
        mock_extract: MagicMock,
        mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        """When issue_number is provided, it's used directly (no branch extraction)."""
        mock_mgr = MagicMock()
        mock_issue_mgr_cls.return_value = mock_mgr

        handle_workflow_failure(
            failure=failure,
            comment_body="Comment body",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
            issue_number=99,
        )

        mock_mgr.add_comment.assert_called_once_with(99, "Comment body")
        # Branch extraction should not be called when issue_number is provided
        mock_extract.assert_not_called()
        mock_branch.assert_not_called()

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_extracts_issue_number_from_branch_when_not_provided(
        self,
        mock_extract: MagicMock,
        mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        mock_branch.return_value = "55-my-feature"
        mock_extract.return_value = 55
        mock_mgr = MagicMock()
        mock_issue_mgr_cls.return_value = mock_mgr

        handle_workflow_failure(
            failure=failure,
            comment_body="Comment body",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
        )

        mock_branch.assert_called_once_with(Path("/fake"))
        mock_extract.assert_called_once_with("55-my-feature")
        mock_mgr.add_comment.assert_called_once_with(55, "Comment body")

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_label_failure_does_not_raise(
        self,
        _mock_extract: MagicMock,
        _mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        _mock_branch.return_value = None
        mock_mgr = MagicMock()
        mock_mgr.update_workflow_label.side_effect = RuntimeError("GitHub API error")
        mock_issue_mgr_cls.return_value = mock_mgr

        # Should not raise
        handle_workflow_failure(
            failure=failure,
            comment_body="Test",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
            update_labels=True,
        )

    @patch("mcp_coder.workflow_utils.failure_handling.IssueManager")
    @patch("mcp_coder.workflow_utils.failure_handling.get_current_branch_name")
    @patch("mcp_coder.workflow_utils.failure_handling.extract_issue_number_from_branch")
    def test_comment_failure_does_not_raise(
        self,
        mock_extract: MagicMock,
        mock_branch: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        failure: WorkflowFailure,
    ) -> None:
        mock_branch.return_value = "10-feat"
        mock_extract.return_value = 10
        mock_mgr = MagicMock()
        mock_mgr.add_comment.side_effect = RuntimeError("GitHub API error")
        mock_issue_mgr_cls.return_value = mock_mgr

        # Should not raise
        handle_workflow_failure(
            failure=failure,
            comment_body="Test",
            project_dir=Path("/fake"),
            from_label_id="pr_creating",
        )
