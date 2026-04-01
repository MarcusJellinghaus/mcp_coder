"""Tests for create-pr workflow failure handling paths."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import (
    _format_failure_comment,
    _handle_create_pr_failure,
    run_create_pr_workflow,
)


class TestFormatFailureComment:
    """Tests for _format_failure_comment."""

    def test_basic_failure_comment(self) -> None:
        """Test basic comment with stage and message only."""
        comment = _format_failure_comment(
            stage="prerequisites",
            message="Working directory not clean",
        )
        assert "## PR Creation Failed" in comment
        assert "**Stage:** prerequisites" in comment
        assert "**Error:** Working directory not clean" in comment
        assert "**Elapsed:**" not in comment
        assert "**PR:**" not in comment

    def test_comment_with_elapsed_time(self) -> None:
        """Test comment includes elapsed time when provided."""
        comment = _format_failure_comment(
            stage="push",
            message="Push failed",
            elapsed_time=125.0,
        )
        assert "**Elapsed:** 2m 5s" in comment

    def test_comment_with_pr_link(self) -> None:
        """Test comment includes PR link when provided."""
        comment = _format_failure_comment(
            stage="cleanup",
            message="Cleanup failed",
            pr_url="https://github.com/test/repo/pull/42",
            pr_number=42,
        )
        assert "**PR:** [42](https://github.com/test/repo/pull/42)" in comment

    def test_cleanup_failure_notes_pr_info_exists(self) -> None:
        """Test cleanup failure adds note about pr_info directory."""
        comment = _format_failure_comment(
            stage="cleanup",
            message="Cleanup failed",
            is_cleanup_failure=True,
        )
        assert "pr_info/ directory may still exist on the branch" in comment


class TestCreatePrFailureHandling:
    """Tests for failure handling in run_create_pr_workflow."""

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_prerequisites_failure_sets_label_and_posts_comment(
        self, mock_prereqs: MagicMock, mock_handle_failure: MagicMock
    ) -> None:
        """Test prerequisites failure calls failure handler."""
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude", update_labels=True)

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "prerequisites"
        assert call_kwargs["update_labels"] is True

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    def test_summary_generation_failure(
        self,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test summary generation failure calls failure handler."""
        mock_prereqs.return_value = True
        mock_generate.side_effect = RuntimeError("LLM connection lost")

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "summary_generation"
        assert "LLM connection lost" in call_kwargs["message"]

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    def test_push_failure_is_fatal(
        self,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test pre-PR push failure is now fatal (returns 1)."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": False, "error": "remote rejected"}

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "push"
        assert "remote rejected" in call_kwargs["message"]

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    def test_pr_creation_failure(
        self,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test PR creation failure calls failure handler."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = None

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "pr_creation"

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    def test_cleanup_failure_includes_pr_link(
        self,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test cleanup failure includes PR URL and number."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = {
            "number": 42,
            "url": "https://github.com/test/repo/pull/42",
        }
        mock_cleanup.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "cleanup"
        assert call_kwargs["pr_url"] == "https://github.com/test/repo/pull/42"
        assert call_kwargs["pr_number"] == 42
        assert call_kwargs["is_cleanup_failure"] is True

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    def test_cleanup_commit_failure(
        self,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test commit failure during cleanup calls failure handler."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = {
            "number": 42,
            "url": "https://github.com/test/repo/pull/42",
        }
        mock_cleanup.return_value = True
        mock_clean.return_value = False  # Has changes
        mock_commit.return_value = {"success": False, "error": "commit hook failed"}

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "cleanup"
        assert "commit hook failed" in call_kwargs["message"]
        assert call_kwargs["is_cleanup_failure"] is True

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    def test_cleanup_push_failure(
        self,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test push failure during cleanup calls failure handler."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        # First push succeeds (pre-PR), second push fails (cleanup)
        mock_push.side_effect = [
            {"success": True},
            {"success": False, "error": "network timeout"},
        ]
        mock_create_pr.return_value = {
            "number": 42,
            "url": "https://github.com/test/repo/pull/42",
        }
        mock_cleanup.return_value = True
        mock_clean.return_value = False  # Has changes
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "cleanup"
        assert "network timeout" in call_kwargs["message"]
        assert call_kwargs["is_cleanup_failure"] is True

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_safety_net_fires_on_unexpected_exception(
        self, mock_prereqs: MagicMock, mock_handle_failure: MagicMock
    ) -> None:
        """Test safety net fires when unexpected exception occurs."""
        mock_prereqs.side_effect = RuntimeError("Unexpected crash")

        with pytest.raises(RuntimeError, match="Unexpected crash"):
            run_create_pr_workflow(Path("/test"), "claude")

        # Safety net should have called _handle_create_pr_failure
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "unexpected"

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_safety_net_skipped_on_normal_failure(
        self, mock_prereqs: MagicMock, mock_handle_failure: MagicMock
    ) -> None:
        """Test safety net does NOT fire when failure is handled normally."""
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        # Only one call - from the prerequisites failure, not safety net
        mock_handle_failure.assert_called_once()
        assert mock_handle_failure.call_args.kwargs["stage"] == "prerequisites"

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_comment_posted_even_when_update_labels_false(
        self,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test failure handler is called even when update_labels=False."""
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude", update_labels=False)

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["update_labels"] is False

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_label_not_set_when_update_labels_false(
        self,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test update_labels=False is passed through to handler."""
        mock_validate.return_value = 123
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude", update_labels=False)

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["update_labels"] is False
