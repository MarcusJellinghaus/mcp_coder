"""Tests for implement workflow failure routing (reason -> failure label).

Split out of test_core_workflow.py, which sits close to the CI file-size gate
(`mcp-coder check file-size --max-lines 750`).
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_processing import TaskOutcome

# Deliberate in-body failures go through implement's `_fail` -> this handler.
# (The SIGTERM / unexpected-exit net lives in run_guarded and is exercised in
# test_core_workflow.py, not here.)
_DELIBERATE_HANDLER = (
    "mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure"
)


class TestRunImplementWorkflowFailureRouting:
    """Test that each task-processing reason routes to the right failure label."""

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_timeout_calls_handle_failure_with_llm_timeout(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """When LLM times out, deliberate failure labels llm_timeout."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "timeout")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "llm_timeout"
        assert failure_arg.stage == "Task implementation"

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_mcp_unavailable_calls_handle_failure_with_mcp_unavailable(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """reason 'mcp_unavailable' routes to mcp_unavailable failure handling."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "mcp_unavailable")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "mcp_unavailable"
        assert failure_arg.stage == "Task implementation"

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_no_changes_after_retries_routes_to_failure(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """No changes after retries routes to no_changes_after_retries failure."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "no_changes_after_retries")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "no_changes_after_retries"
        assert failure_arg.stage == "Task implementation"

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_error_calls_handle_failure_with_general(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """When task errors, deliberate failure labels implementing_failed."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "error")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "implementing_failed"
        assert failure_arg.stage == "Task implementation"


class TestBlockedRouting:
    """Test that an agent-reported blocked marker terminates the run."""

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_blocked_routes_to_failure(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """reason 'blocked' labels implementation_blocked with the agent's text."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(
            False, "blocked", "pytest times out at 300s"
        )

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "implementation_blocked"
        assert failure_arg.stage == "Task implementation"
        assert failure_arg.message == "pytest times out at 300s"

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_blocked_does_not_loop(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """blocked is terminal - the task loop does not run a second attempt."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "blocked", "cannot verify")

        run_implement_workflow(Path("/project"), "claude")

        assert mock_process.call_count == 1

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_blocked_reason_logged_at_error(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The reason is logged at ERROR even when comment posting is off."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(
            False, "blocked", "mcp-tools-py pytest never returns"
        )

        with caplog.at_level(
            logging.ERROR, logger="mcp_coder.workflows.implement.core"
        ):
            run_implement_workflow(
                Path("/project"), "claude", post_issue_comments=False
            )

        assert "mcp-tools-py pytest never returns" in caplog.text

    @patch(_DELIBERATE_HANDLER)
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_timeout_appends_marker_detail(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """A marker alongside a timeout keeps llm_timeout but carries the text."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "timeout", "why")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "llm_timeout"
        assert "LLM timed out during task processing" in failure_arg.message
        assert "why" in failure_arg.message
