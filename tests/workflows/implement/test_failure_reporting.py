"""Tests for implement workflow failure reporting helpers."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.failure_reporting import (
    CATEGORY_DISPLAY,
    FAILURE_LABELS,
    Progress,
    _fail,
    append_detail,
    format_failure_comment,
)
from mcp_coder.workflows.implement.task_processing import TaskOutcome


class TestFailureLabels:
    """Tests for the FAILURE_LABELS reason -> label mapping."""

    def test_labels_match_label_ids(self) -> None:
        """Reason strings map to the expected labels.json internal IDs."""
        assert FAILURE_LABELS["general"] == "implementing_failed"
        assert FAILURE_LABELS["timeout"] == "llm_timeout"
        assert FAILURE_LABELS["mcp_unavailable"] == "mcp_unavailable"
        assert FAILURE_LABELS["task_tracker_prep_failed"] == "task_tracker_prep_failed"
        assert FAILURE_LABELS["no_changes_after_retries"] == "no_changes_after_retries"
        assert FAILURE_LABELS["ci_fix_exhausted"] == "ci_fix_needed"

    def test_blocked_maps_to_implementation_blocked(self) -> None:
        """The agent-reported blocked reason gets its own terminal label."""
        assert FAILURE_LABELS["blocked"] == "implementation_blocked"
        assert CATEGORY_DISPLAY["blocked"] == "Blocked"


class TestAppendDetail:
    """Tests for append_detail."""

    def test_empty_detail_returns_message_unchanged(self) -> None:
        """No marker text -> the base message is returned as-is."""
        assert append_detail("base", "") == "base"

    def test_detail_is_appended(self) -> None:
        """Marker text is appended to the base message, keeping both."""
        result = append_detail("base", "why")

        assert "base" in result
        assert "why" in result


class TestFormatFailureComment:
    """Tests for format_failure_comment."""

    def test_basic_failure_comment(self) -> None:
        """Formats basic failure comment with category, stage, error."""
        result = format_failure_comment(
            "general",
            "test stage",
            "something failed",
            completed=0,
            total=0,
            elapsed=None,
            build_url=None,
            diff_stat="",
        )

        assert "## Implementation Failed" in result
        assert "General" in result
        assert "test stage" in result
        assert "something failed" in result
        assert "No uncommitted changes" in result

    def test_timeout_renders_llm_timeout_category(self) -> None:
        """Reason 'timeout' renders 'Llm Timeout' (not 'Timeout')."""
        result = format_failure_comment(
            "timeout",
            "Task implementation",
            "timed out",
            completed=0,
            total=0,
            elapsed=None,
            build_url=None,
            diff_stat="",
        )

        assert "**Category:** Llm Timeout" in result

    def test_blocked_renders_blocked_category(self) -> None:
        """Reason 'blocked' renders 'Blocked' with the agent's text as Error."""
        result = format_failure_comment(
            "blocked",
            "Task implementation",
            "pytest times out at 300s",
            completed=0,
            total=0,
            elapsed=None,
            build_url=None,
            diff_stat="",
        )

        assert "**Category:** Blocked" in result
        assert "**Error:** pytest times out at 300s" in result

    def test_includes_progress_when_set(self) -> None:
        """Includes progress info when total > 0."""
        result = format_failure_comment(
            "timeout",
            "Task implementation",
            "timed out",
            completed=2,
            total=5,
            elapsed=None,
            build_url=None,
            diff_stat="file.py | 3 +++",
        )

        assert "2/5" in result
        assert "file.py" in result

    def test_no_progress_when_zero_total(self) -> None:
        """No progress line when total is 0."""
        result = format_failure_comment(
            "general",
            "test",
            "failed",
            completed=0,
            total=0,
            elapsed=None,
            build_url=None,
            diff_stat="",
        )

        assert "Progress" not in result

    def test_includes_elapsed_time_when_set(self) -> None:
        """Includes elapsed time line when elapsed is set."""
        comment = format_failure_comment(
            "general",
            "Test",
            "err",
            completed=0,
            total=0,
            elapsed=754.0,
            build_url=None,
            diff_stat="",
        )
        assert "**Elapsed:** 12m 34s" in comment

    def test_includes_build_url_when_set(self) -> None:
        """Includes build URL line when build_url is set."""
        comment = format_failure_comment(
            "general",
            "Test",
            "err",
            completed=0,
            total=0,
            elapsed=None,
            build_url="https://jenkins.example.com/job/123/console",
            diff_stat="",
        )
        assert "**Build:** https://jenkins.example.com/job/123/console" in comment

    def test_excludes_elapsed_time_when_none(self) -> None:
        """Excludes elapsed time line when elapsed is None."""
        comment = format_failure_comment(
            "general",
            "Test",
            "err",
            completed=0,
            total=0,
            elapsed=None,
            build_url=None,
            diff_stat="",
        )
        assert "Elapsed" not in comment

    def test_excludes_build_url_when_none(self) -> None:
        """Excludes build URL line when build_url is None."""
        comment = format_failure_comment(
            "general",
            "Test",
            "err",
            completed=0,
            total=0,
            elapsed=None,
            build_url=None,
            diff_stat="",
        )
        assert "Build" not in comment

    def test_includes_both_elapsed_and_build_url(self) -> None:
        """Includes both elapsed time and build URL when both are set."""
        comment = format_failure_comment(
            "general",
            "Test",
            "err",
            completed=0,
            total=0,
            elapsed=3661.0,
            build_url="https://jenkins.example.com/job/1/console",
            diff_stat="some diff",
        )
        assert "**Elapsed:** 1h 1m 1s" in comment
        assert "**Build:** https://jenkins.example.com/job/1/console" in comment


class TestFail:
    """Tests for the _fail deliberate-failure helper."""

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_returns_one(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """_fail always returns 1 (a deliberate terminal exit code)."""
        mock_diff.return_value = ""

        result = _fail(
            Path("/project"),
            "general",
            stage="test",
            message="failed",
            progress=Progress(),
            start_time=time.time(),
            build_url=None,
        )

        assert result == 1

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_sets_general_label(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """reason 'general' maps to the implementing_failed label."""
        mock_diff.return_value = ""

        _fail(
            Path("/project"),
            "general",
            stage="test",
            message="failed",
            progress=Progress(),
            start_time=time.time(),
            build_url=None,
            update_issue_labels=True,
        )

        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "implementing_failed"
        assert call_kwargs["from_label_id"] == "implementing"
        assert call_kwargs["update_issue_labels"] is True

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_timeout_sets_llm_timeout_label(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """reason 'timeout' maps to the llm_timeout label."""
        mock_diff.return_value = ""

        _fail(
            Path("/project"),
            "timeout",
            stage="Task implementation",
            message="timed out",
            progress=Progress(),
            start_time=time.time(),
            build_url=None,
            update_issue_labels=True,
        )

        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "llm_timeout"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_ci_exhaustion_sets_ci_fix_needed_label(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """reason 'ci_fix_exhausted' maps to the ci_fix_needed label."""
        mock_diff.return_value = ""

        _fail(
            Path("/project"),
            "ci_fix_exhausted",
            stage="CI pipeline fix",
            message="CI failed",
            progress=Progress(),
            start_time=time.time(),
            build_url=None,
            update_issue_labels=True,
        )

        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "ci_fix_needed"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_passes_formatted_comment(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """_fail passes a formatted comment carrying progress and diff stat."""
        mock_diff.return_value = "file.py | 3 +++"

        _fail(
            Path("/project"),
            "timeout",
            stage="Task implementation",
            message="timed out",
            progress=Progress(completed=2, total=5),
            start_time=time.time(),
            build_url=None,
            update_issue_labels=True,
        )

        comment = mock_handle.call_args[1]["comment_body"]
        assert "Implementation Failed" in comment
        assert "Llm Timeout" in comment
        assert "2/5" in comment
        assert "file.py" in comment

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    def test_skips_label_when_update_issue_labels_disabled(
        self,
        mock_diff: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        """When update_issue_labels=False, the flag is forwarded."""
        mock_diff.return_value = ""

        _fail(
            Path("/project"),
            "general",
            stage="test",
            message="failed",
            progress=Progress(),
            start_time=time.time(),
            build_url=None,
            update_issue_labels=False,
        )

        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["update_issue_labels"] is False


class TestDeliberateFailurePathsThroughWorkflow:
    """End-to-end checks that deliberate failure paths label + comment correctly."""

    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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
    @patch.dict(
        "os.environ", {"BUILD_URL": "https://jenkins.example.com/job/2/console"}
    )
    def test_task_tracker_prep_failure_includes_build_url_and_elapsed(
        self,
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
        mock_handle: MagicMock,
        mock_diff: MagicMock,
    ) -> None:
        """Task-tracker-prep failure labels task_tracker_prep_failed w/ build+elapsed."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_diff.return_value = ""
        mock_prepare.return_value = False  # Trigger failure at task tracker preparation

        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 1
        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "task_tracker_prep_failed"
        assert call_kwargs["failure"].elapsed_time is not None
        assert call_kwargs["failure"].elapsed_time >= 0
        assert (
            "https://jenkins.example.com/job/2/console" in call_kwargs["comment_body"]
        )

    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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
    @patch.dict("os.environ", {}, clear=True)
    def test_build_url_absent_when_env_not_set(
        self,
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
        mock_handle: MagicMock,
        mock_diff: MagicMock,
    ) -> None:
        """No Build line in the comment when BUILD_URL env var is not set."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_diff.return_value = ""
        mock_prepare.return_value = False  # Trigger failure

        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 1
        mock_handle.assert_called_once()
        assert "**Build:**" not in mock_handle.call_args[1]["comment_body"]

    @patch("mcp_coder.workflows.implement.failure_reporting.get_diff_stat")
    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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
    @patch.dict(
        "os.environ", {"BUILD_URL": "https://jenkins.example.com/job/5/console"}
    )
    def test_timeout_failure_labels_llm_timeout_with_build_url(
        self,
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
        mock_handle: MagicMock,
        mock_diff: MagicMock,
    ) -> None:
        """Timeout failure labels llm_timeout and carries build url + elapsed."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_diff.return_value = ""
        mock_prepare.return_value = True
        mock_process.return_value = TaskOutcome(False, "timeout")

        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 1
        mock_handle.assert_called_once()
        call_kwargs = mock_handle.call_args[1]
        assert call_kwargs["failure"].category == "llm_timeout"
        assert call_kwargs["failure"].elapsed_time is not None
        assert call_kwargs["failure"].elapsed_time >= 0
        assert (
            "https://jenkins.example.com/job/5/console" in call_kwargs["comment_body"]
        )
