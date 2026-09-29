"""Tests for the progress gate and the retry loop's reason selection."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflow_steps.constants import BLOCKED_FILE
from mcp_coder.workflows.implement.task_processing import (
    NO_PROGRESS_REMINDER,
    RETRY_REMINDER,
    TaskOutcome,
    process_single_task,
    process_task_with_retry,
)


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
