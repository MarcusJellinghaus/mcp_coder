"""Tests for implement workflow failure reporting helpers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.constants import FailureCategory, WorkflowFailure
from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.failure_reporting import (
    _format_failure_comment,
    _handle_workflow_failure,
)


class TestFormatFailureComment:
    """Tests for _format_failure_comment."""

    def test_basic_failure_comment(self) -> None:
        """Formats basic failure comment with category, stage, error."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test stage",
            message="something failed",
        )
        result = _format_failure_comment(failure, "")

        assert "## Implementation Failed" in result
        assert "General" in result
        assert "test stage" in result
        assert "something failed" in result
        assert "No uncommitted changes" in result

    def test_includes_progress_when_set(self) -> None:
        """Includes progress info when tasks_total > 0."""
        failure = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="Task implementation",
            message="timed out",
            tasks_completed=2,
            tasks_total=5,
        )
        result = _format_failure_comment(failure, "file.py | 3 +++")

        assert "2/5" in result
        assert "file.py" in result

    def test_no_progress_when_zero_total(self) -> None:
        """No progress line when tasks_total is 0."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="failed",
        )
        result = _format_failure_comment(failure, "")

        assert "Progress" not in result


class TestHandleWorkflowFailure:
    """Tests for _handle_workflow_failure."""

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_sets_failure_label(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """Failure handler delegates to shared handler with correct category."""
        mock_diff.return_value = ""

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="failed",
        )
        _handle_workflow_failure(failure, Path("/project"), update_issue_labels=True)

        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "implementing_failed"
        assert call_kwargs["from_label_id"] == "implementing"
        assert call_kwargs["update_issue_labels"] is True

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_posts_github_comment(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """Failure handler passes formatted comment to shared handler."""
        mock_diff.return_value = "file.py | 3 +++"

        failure = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="Task implementation",
            message="timed out",
            tasks_completed=2,
            tasks_total=5,
        )
        _handle_workflow_failure(failure, Path("/project"), update_issue_labels=True)

        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        comment = call_kwargs["comment_body"]
        assert "Implementation Failed" in comment
        assert "Llm Timeout" in comment
        assert "2/5" in comment
        assert "file.py" in comment

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_label_error_non_blocking(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """Shared handler is called; error handling is its responsibility."""
        mock_diff.return_value = ""

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="failed",
        )
        _handle_workflow_failure(failure, Path("/project"), update_issue_labels=True)

        mock_handle.assert_called_once()

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_ci_exhaustion_sets_ci_fix_needed_label(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """CI fix exhaustion passes ci_fix_needed category to shared handler."""
        mock_diff.return_value = ""

        failure = WorkflowFailure(
            category=FailureCategory.CI_FIX_EXHAUSTED,
            stage="CI pipeline fix",
            message="CI failed",
        )
        _handle_workflow_failure(failure, Path("/project"), update_issue_labels=True)

        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "ci_fix_needed"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_timeout_sets_llm_timeout_label(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """LLM timeout passes llm_timeout category to shared handler."""
        mock_diff.return_value = ""

        failure = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="Task implementation",
            message="timed out",
        )
        _handle_workflow_failure(failure, Path("/project"), update_issue_labels=True)

        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "llm_timeout"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_handle_workflow_failure_skips_label_when_update_issue_labels_disabled(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """When update_issue_labels=False, flag is passed to shared handler."""
        mock_diff.return_value = ""

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="failed",
        )
        _handle_workflow_failure(failure, Path("/project"), update_issue_labels=False)

        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["update_issue_labels"] is False


class TestFormatFailureCommentElapsedAndBuildUrl:
    """Tests for elapsed time and build URL in _format_failure_comment."""

    def test_includes_elapsed_time_when_set(self) -> None:
        """Includes elapsed time line when elapsed_time is set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="Test",
            message="err",
            elapsed_time=754.0,
        )
        comment = _format_failure_comment(failure, "")
        assert "**Elapsed:** 12m 34s" in comment

    def test_includes_build_url_when_set(self) -> None:
        """Includes build URL line when build_url is set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="Test",
            message="err",
            build_url="https://jenkins.example.com/job/123/console",
        )
        comment = _format_failure_comment(failure, "")
        assert "**Build:** https://jenkins.example.com/job/123/console" in comment

    def test_excludes_elapsed_time_when_none(self) -> None:
        """Excludes elapsed time line when elapsed_time is None."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="Test",
            message="err",
        )
        comment = _format_failure_comment(failure, "")
        assert "Elapsed" not in comment

    def test_excludes_build_url_when_none(self) -> None:
        """Excludes build URL line when build_url is None."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="Test",
            message="err",
        )
        comment = _format_failure_comment(failure, "")
        assert "Build" not in comment

    def test_includes_both_elapsed_and_build_url(self) -> None:
        """Includes both elapsed time and build URL when both are set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="Test",
            message="err",
            elapsed_time=3661.0,
            build_url="https://jenkins.example.com/job/1/console",
        )
        comment = _format_failure_comment(failure, "some diff")
        assert "**Elapsed:** 1h 1m 1s" in comment
        assert "**Build:** https://jenkins.example.com/job/1/console" in comment


class TestExistingFailuresIncludeNewFields:
    """Tests that existing WorkflowFailure constructions include build_url and elapsed_time."""

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch.dict(
        "os.environ", {"BUILD_URL": "https://jenkins.example.com/job/2/console"}
    )
    def test_existing_failures_include_build_url_and_elapsed(
        self,
        mock_handle_failure: MagicMock,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        _mock_finalisation: MagicMock,
        mock_branch: MagicMock,
        mock_ci: MagicMock,
    ) -> None:
        """Existing handled failures include build_url and elapsed_time."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = False  # Trigger failure at task tracker preparation

        run_implement_workflow(Path("/fake"), "claude")

        mock_handle_failure.assert_called_once()
        failure = mock_handle_failure.call_args[0][0]
        assert failure.build_url == "https://jenkins.example.com/job/2/console"
        assert failure.elapsed_time is not None
        assert failure.elapsed_time >= 0

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch.dict("os.environ", {}, clear=True)
    def test_build_url_none_when_env_not_set(
        self,
        mock_handle_failure: MagicMock,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        _mock_finalisation: MagicMock,
        mock_branch: MagicMock,
        mock_ci: MagicMock,
    ) -> None:
        """build_url is None when BUILD_URL env var is not set."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = False  # Trigger failure

        run_implement_workflow(Path("/fake"), "claude")

        mock_handle_failure.assert_called_once()
        failure = mock_handle_failure.call_args[0][0]
        assert failure.build_url is None

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch.dict(
        "os.environ", {"BUILD_URL": "https://jenkins.example.com/job/5/console"}
    )
    def test_timeout_failure_includes_build_url_and_elapsed(
        self,
        mock_handle_failure: MagicMock,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        _mock_finalisation: MagicMock,
        mock_branch: MagicMock,
        mock_ci: MagicMock,
    ) -> None:
        """Timeout failures include build_url and elapsed_time."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "timeout")

        run_implement_workflow(Path("/fake"), "claude")

        mock_handle_failure.assert_called_once()
        failure = mock_handle_failure.call_args[0][0]
        assert failure.category == FailureCategory.LLM_TIMEOUT
        assert failure.build_url == "https://jenkins.example.com/job/5/console"
        assert failure.elapsed_time is not None
        assert failure.elapsed_time >= 0
