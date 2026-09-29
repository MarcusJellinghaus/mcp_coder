"""Tests for the progress gate and the retry loop's reason selection."""

import itertools
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.constants import BLOCKED_FILE
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
)
from mcp_coder.workflows.implement.task_processing import (
    NO_PROGRESS_REMINDER,
    RETRY_REMINDER,
    TaskOutcome,
    _count_incomplete_tasks,
    process_single_task,
    process_task_with_retry,
)

_TP = "mcp_coder.workflows.implement.task_processing"


@pytest.fixture(autouse=True)
def _tracker_count_always_decreases(request: pytest.FixtureRequest) -> Iterator[None]:
    """Make every progress-gate read look like progress unless opted out."""
    if request.node.get_closest_marker("real_tracker_count"):
        yield
        return
    with patch(
        f"{_TP}._count_incomplete_tasks",
        side_effect=itertools.count(5, -1),
    ):
        yield


def _make_llm_response(text: str = "LLM response") -> dict[str, object]:
    """Create a minimal LLMResponseDict-compatible dict for mocking."""
    return {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": text,
        "session_id": "test-session-id",
        "provider": "claude",
        "raw_response": {},
    }


class TestRetryTerminalReason:
    """process_task_with_retry picks the terminal reason from the attempts."""

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_all_no_progress_returns_no_progress_after_retries(
        self, mock_single: MagicMock
    ) -> None:
        """Three no-progress attempts exhaust the budget with the new reason."""
        mock_single.return_value = TaskOutcome(False, "no_progress", "Step 2: Thing")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "no_progress_after_retries"
        assert outcome.detail == "Step 2: Thing"

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_all_no_changes_returns_no_changes_after_retries(
        self, mock_single: MagicMock
    ) -> None:
        """Zero-change attempts keep the pre-existing terminal reason."""
        mock_single.return_value = TaskOutcome(False, "no_changes")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.reason == "no_changes_after_retries"
        assert outcome.detail == ""

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_mixed_sequence_keeps_no_progress_and_its_detail(
        self, mock_single: MagicMock
    ) -> None:
        """A trailing zero-change attempt erases neither the reason nor the detail."""
        mock_single.side_effect = [
            TaskOutcome(False, "no_changes"),
            TaskOutcome(False, "no_progress", "Step 2: Thing"),
            TaskOutcome(False, "no_changes"),
        ]

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.reason == "no_progress_after_retries"
        assert outcome.detail == "Step 2: Thing"

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_success_after_no_progress_returned_unchanged(
        self, mock_single: MagicMock
    ) -> None:
        """Any other reason short-circuits the loop and is returned as-is."""
        success = TaskOutcome(True, "completed")
        mock_single.side_effect = [TaskOutcome(False, "no_progress"), success]

        assert process_task_with_retry(Path("/test/project"), "claude") is success


class TestPreviousReasonForwarding:
    """The retry loop tells each attempt what the previous one did."""

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_first_attempt_has_no_previous_reason(self, mock_single: MagicMock) -> None:
        """Attempt 1 has no predecessor, so it gets None."""
        mock_single.return_value = TaskOutcome(True, "completed")

        process_task_with_retry(Path("/test/project"), "claude")

        assert mock_single.call_args.kwargs["previous_reason"] is None

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_attempt_after_no_progress_gets_no_progress(
        self, mock_single: MagicMock
    ) -> None:
        """Attempt 2 is told the previous attempt changed files without progress."""
        mock_single.side_effect = [
            TaskOutcome(False, "no_progress"),
            TaskOutcome(True, "completed"),
        ]

        process_task_with_retry(Path("/test/project"), "claude")

        assert mock_single.call_args.kwargs["previous_reason"] == "no_progress"

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_attempt_after_no_changes_gets_no_changes(
        self, mock_single: MagicMock
    ) -> None:
        """Attempt 2 after a zero-change attempt is told so."""
        mock_single.side_effect = [
            TaskOutcome(False, "no_changes"),
            TaskOutcome(True, "completed"),
        ]

        process_task_with_retry(Path("/test/project"), "claude")

        assert mock_single.call_args.kwargs["previous_reason"] == "no_changes"


class TestReminderSelection:
    """process_single_task appends the reminder matching previous_reason."""

    @staticmethod
    def _prompt_for(previous_reason: str | None) -> str:
        with (
            patch("mcp_coder.workflows.implement.task_processing.store_session"),
            patch(
                "mcp_coder.workflows.implement.task_processing.prompt_llm"
            ) as mock_prompt_llm,
            patch(
                "mcp_coder.workflows.implement.task_processing.get_prompt",
                return_value="Template",
            ),
            patch(
                "mcp_coder.workflows.implement.task_processing.get_next_task",
                return_value="Step 1: Test task",
            ),
            patch(
                "mcp_coder.workflows.implement.task_processing.get_full_status",
                side_effect=Exception("stop here"),
            ),
        ):
            mock_prompt_llm.return_value = _make_llm_response("Response")
            process_single_task(
                Path("/test/project"),
                "claude",
                attempt=2,
                previous_reason=previous_reason,
            )
            call_args = mock_prompt_llm.call_args
            prompt: str = call_args[0][0] if call_args[0] else call_args[1]["prompt"]
            return prompt

    def test_no_progress_selects_its_own_reminder(self) -> None:
        """previous_reason='no_progress' swaps in the no-progress wording."""
        prompt = self._prompt_for("no_progress")

        assert NO_PROGRESS_REMINDER in prompt
        assert RETRY_REMINDER not in prompt

    def test_missing_previous_reason_falls_back_to_retry_reminder(self) -> None:
        """Without a previous reason, the pre-existing reminder is used."""
        assert RETRY_REMINDER in self._prompt_for(None)


class TestNoProgressReminderText:
    """The new reminder wording."""

    def test_offers_blocked_exit(self) -> None:
        """It points at the blocked marker instead of demanding a tick."""
        assert BLOCKED_FILE in NO_PROGRESS_REMINDER

    def test_names_no_specific_task(self) -> None:
        """A retry may target a different task, so the text must not name one."""
        assert "Step 1" not in NO_PROGRESS_REMINDER
        assert "Step 2" not in NO_PROGRESS_REMINDER


class TestProgressGate:
    """process_single_task scores a round by the incomplete-task count."""

    TASK = "Step 2: Implement thing"

    @staticmethod
    def _run(
        count: MagicMock,
        next_task: MagicMock | None = None,
        changes: list[str] | None = None,
    ) -> tuple[TaskOutcome, MagicMock, MagicMock]:
        """Run one round with everything but the tracker reads mocked."""
        status = {
            "staged": [],
            "modified": ["src/x.py"] if changes is None else changes,
            "untracked": [],
        }
        with (
            patch(f"{_TP}._count_incomplete_tasks", count),
            patch(
                f"{_TP}.get_next_task",
                next_task or MagicMock(return_value=TestProgressGate.TASK),
            ),
            patch(f"{_TP}.get_prompt", return_value="Template"),
            patch(f"{_TP}.prompt_llm", return_value=_make_llm_response()),
            patch(f"{_TP}.store_session"),
            patch(f"{_TP}.get_full_status", return_value=status),
            patch(f"{_TP}.commit_changes", return_value=True) as mock_commit,
            patch(f"{_TP}.push_changes", return_value=True) as mock_push,
        ):
            outcome = process_single_task(Path("/test/project"), "claude")
        return outcome, mock_commit, mock_push

    def test_count_decreased_is_completed(self) -> None:
        """A lower count after the round is progress."""
        outcome, _, _ = self._run(MagicMock(side_effect=[3, 2]))

        assert outcome == TaskOutcome(True, "completed")

    def test_flat_count_is_no_progress_but_still_committed(self) -> None:
        """Changed files without a tick are committed, then scored no_progress."""
        outcome, mock_commit, mock_push = self._run(MagicMock(side_effect=[3, 3]))

        assert outcome == TaskOutcome(False, "no_progress", self.TASK)
        mock_commit.assert_called_once()
        mock_push.assert_called_once()

    def test_rising_count_is_no_progress(self) -> None:
        """Adding tasks is not progress."""
        outcome, _, _ = self._run(MagicMock(side_effect=[3, 4]))

        assert outcome.reason == "no_progress"

    def test_after_read_failure_is_no_progress(self) -> None:
        """An unreadable tracker after the round scores no_progress, not a crash."""
        outcome, _, _ = self._run(
            MagicMock(side_effect=[3, TaskTrackerFileNotFoundError("gone")])
        )

        assert outcome == TaskOutcome(False, "no_progress", self.TASK)

    def test_missing_tracker_before_round_is_error(self) -> None:
        """A missing tracker fails loudly instead of reading as 'no tasks'."""
        next_task = MagicMock(
            side_effect=TaskTrackerFileNotFoundError("TASK_TRACKER.md not found")
        )

        outcome, mock_commit, _ = self._run(MagicMock(), next_task=next_task)

        assert outcome.reason == "error"
        assert "TASK_TRACKER.md" in outcome.detail
        mock_commit.assert_not_called()

    def test_missing_section_before_round_is_error(self) -> None:
        """A tracker without a tasks section names the section fault."""
        next_task = MagicMock(
            side_effect=TaskTrackerSectionNotFoundError("Tasks section not found")
        )

        outcome, _, _ = self._run(MagicMock(), next_task=next_task)

        assert outcome.reason == "error"
        assert "TASK_TRACKER.md" in outcome.detail
        assert "Tasks section not found" in outcome.detail

    @pytest.mark.parametrize(
        "exc",
        [
            OSError("permission denied"),
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
        ],
    )
    def test_non_tracker_error_before_round_is_error(self, exc: Exception) -> None:
        """Read failures outside TaskTrackerError still map to 'error'."""
        outcome, _, _ = self._run(MagicMock(), next_task=MagicMock(side_effect=exc))

        assert outcome.reason == "error"
        assert "TASK_TRACKER.md" in outcome.detail
        assert type(exc).__name__ in outcome.detail

    def test_zero_changes_still_no_changes(self) -> None:
        """The zero-change gate runs first and wins."""
        outcome, mock_commit, _ = self._run(MagicMock(side_effect=[3, 3]), changes=[])

        assert outcome == TaskOutcome(False, "no_changes")
        mock_commit.assert_not_called()


@pytest.mark.real_tracker_count
class TestCountIncompleteTasks:
    """_count_incomplete_tasks against a real tracker file."""

    def test_counts_non_meta_incomplete_tasks_under_pr_info(
        self, tmp_path: Path
    ) -> None:
        """Pins both the pr_info path derivation and the meta-task exclusion."""
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "TASK_TRACKER.md").write_text(
            "# Task Status Tracker\n\n"
            "## Implementation Steps\n\n"
            "- [ ] Step 1: First task\n"
            "- [x] Step 1: Done task\n"
            "- [ ] Step 2: Second task\n"
            "- [ ] All Step 1 tasks completed\n",
            encoding="utf-8",
        )

        assert _count_incomplete_tasks(tmp_path) == 2

    def test_missing_pr_info_raises(self, tmp_path: Path) -> None:
        """No tracker file is an error, not zero."""
        with pytest.raises(TaskTrackerFileNotFoundError):
            _count_incomplete_tasks(tmp_path)
