from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.task_processing import (
    TaskOutcome,
    process_task_with_retry,
)


class TestProcessTaskWithRetry:
    """Test process_task_with_retry wrapper function."""

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_retry_succeeds_on_second_attempt(self, mock_process: MagicMock) -> None:
        """First call returns no_changes, second returns completed."""
        mock_process.side_effect = [
            TaskOutcome(False, "no_changes"),
            TaskOutcome(True, "completed"),
        ]

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is True
        assert outcome.reason == "completed"
        assert mock_process.call_count == 2
        # Verify attempt numbers
        assert mock_process.call_args_list[0].kwargs["attempt"] == 1
        assert mock_process.call_args_list[1].kwargs["attempt"] == 2

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_retry_exhausted_returns_no_changes_after_retries(
        self, mock_process: MagicMock
    ) -> None:
        """All 3 calls return no_changes."""
        mock_process.return_value = TaskOutcome(False, "no_changes")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "no_changes_after_retries"
        assert mock_process.call_count == 3

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_timeout_propagates_immediately(self, mock_process: MagicMock) -> None:
        """First call returns timeout — no retry."""
        mock_process.return_value = TaskOutcome(False, "timeout")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "timeout"
        assert mock_process.call_count == 1

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_error_propagates_immediately(self, mock_process: MagicMock) -> None:
        """First call returns error — no retry."""
        mock_process.return_value = TaskOutcome(False, "error")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "error"
        assert mock_process.call_count == 1

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_no_tasks_propagates_immediately(self, mock_process: MagicMock) -> None:
        """First call returns no_tasks — no retry."""
        mock_process.return_value = TaskOutcome(False, "no_tasks")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "no_tasks"
        assert mock_process.call_count == 1

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_success_on_first_attempt_no_retry(self, mock_process: MagicMock) -> None:
        """First call returns completed — no retry."""
        mock_process.return_value = TaskOutcome(True, "completed")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is True
        assert outcome.reason == "completed"
        assert mock_process.call_count == 1

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_timeout_on_second_attempt_propagates(
        self, mock_process: MagicMock
    ) -> None:
        """First call no_changes, second call timeout — propagates immediately."""
        mock_process.side_effect = [
            TaskOutcome(False, "no_changes"),
            TaskOutcome(False, "timeout"),
        ]

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "timeout"
        assert mock_process.call_count == 2

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_mcp_unavailable_categorized_as_reason(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """A McpServersUnavailableError is categorized to the 'mcp_unavailable' reason.

        process_single_task no longer re-raises the typed error; it maps it to a
        stable reason so the orchestrator can select the MCP_UNAVAILABLE
        category/label. process_task_with_retry propagates the reason without
        retrying (reason != 'no_changes').
        """
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )

        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "mcp_unavailable"
        assert mock_prompt_llm.call_count == 1
