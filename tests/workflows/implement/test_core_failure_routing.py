"""Tests for implement workflow failure routing (reason -> failure label).

Split out of test_core_workflow.py, which sits close to the CI file-size gate
(`mcp-coder check file-size --max-lines 750`).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

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
