"""Tests for create-pr workflow failure handling paths."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
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

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "prerequisites"
        assert call_kwargs["update_issue_labels"] is True

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
        # Generic exception → general label
        assert call_kwargs["category"] == "pr_creating_failed"

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    def test_summary_generation_mcp_unavailable_routes_to_mcp_label(
        self,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """MCP-unavailable during summary generation routes to pr_creating_mcp."""
        mock_prereqs.return_value = True
        mock_generate.side_effect = McpServersUnavailableError(
            "boom", unavailable_servers={"mcp-tools-py": "failed"}
        )

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "summary_generation"
        assert call_kwargs["category"] == "pr_creating_mcp"
        # Message is built via the server-naming formatter.
        assert "mcp-tools-py" in call_kwargs["message"]

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    def test_summary_generation_timeout_routes_to_timeout_label(
        self,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """LLM timeout during summary generation routes to pr_creating_timeout."""
        mock_prereqs.return_value = True
        mock_generate.side_effect = LLMTimeoutError("timed out")

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "summary_generation"
        assert call_kwargs["category"] == "pr_creating_timeout"
        assert "timed out" in call_kwargs["message"]

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    def test_push_failure_is_fatal(
        self,
        mock_push: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test pre-PR push failure is now fatal (returns 1)."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_cleanup.return_value = True
        mock_clean.return_value = True
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
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    def test_pr_creation_failure(
        self,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test PR creation failure calls failure handler."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            None,
            "422 Validation Failed: head branch not found",
        )

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "pr_creation"
        assert "422 Validation Failed" in call_kwargs["message"]

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    def test_cleanup_failure_is_fatal(
        self,
        mock_cleanup: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test cleanup failure before push/PR is fatal (no pr_url/pr_number)."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_cleanup.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "cleanup"
        assert "pr_url" not in call_kwargs
        assert "pr_number" not in call_kwargs
        assert "is_cleanup_failure" not in call_kwargs

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    def test_cleanup_commit_failure(
        self,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test commit failure during cleanup calls failure handler."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_cleanup.return_value = True
        mock_clean.return_value = False  # Has changes
        mock_commit.return_value = {"success": False, "error": "commit hook failed"}

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["stage"] == "cleanup"
        assert "commit hook failed" in call_kwargs["message"]
        assert "is_cleanup_failure" not in call_kwargs
        assert "pr_url" not in call_kwargs
        assert "pr_number" not in call_kwargs

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_unexpected_exception_netted_by_guard(
        self,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
        mock_workflow_failure: MagicMock,
    ) -> None:
        """An unexpected escape is netted by run_guarded, not the seam.

        The deliberate ``_handle_create_pr_failure`` seam is bypassed on the
        net path; the guard calls ``handle_workflow_failure`` directly with the
        general ``pr_creating_failed`` label and returns 1 (the escape is
        swallowed for a non-``SystemExit`` exception).
        """
        mock_prereqs.side_effect = RuntimeError("Unexpected crash")

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        # Net path bypasses the deliberate seam entirely.
        mock_handle_failure.assert_not_called()
        # Guard applies the general label via the shared handler.
        mock_workflow_failure.assert_called_once()
        failure = mock_workflow_failure.call_args.args[0]
        assert failure.category == "pr_creating_failed"

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
    def test_comment_posted_even_when_update_issue_labels_false(
        self,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test failure handler is called even when update_issue_labels=False."""
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=False
        )

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["update_issue_labels"] is False

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_label_not_set_when_update_issue_labels_false(
        self,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test update_issue_labels=False is passed through to handler."""
        mock_validate.return_value = 123
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=False
        )

        assert result == 1
        mock_handle_failure.assert_called_once()
        call_kwargs = mock_handle_failure.call_args.kwargs
        assert call_kwargs["update_issue_labels"] is False
