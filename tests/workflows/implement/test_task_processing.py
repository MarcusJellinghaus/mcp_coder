"""Tests for implement workflow task processing."""

from pathlib import Path
from typing import Any, Callable, Optional
from unittest.mock import ANY, MagicMock, patch

import pytest

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.workflow_steps.constants import BLOCKED_FILE
from mcp_coder.workflows.implement.constants import (
    BLOCKED_FILE as IMPLEMENT_BLOCKED_FILE,
)
from mcp_coder.workflows.implement.task_processing import (
    BLOCKED_REASON_FALLBACK,
    BLOCKED_REASON_MAX_CHARS,
    RETRY_REMINDER,
    TaskOutcome,
    _cleanup_commit_message_file,
    check_and_fix_mypy,
    get_next_task,
    process_single_task,
    process_task_with_retry,
    read_and_clear_blocked,
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


class TestGetNextTask:
    """Test get_next_task function."""

    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_get_next_task_success(self, mock_get_incomplete: MagicMock) -> None:
        """Test getting next task when incomplete tasks exist."""
        mock_get_incomplete.return_value = ["Task 1", "Task 2", "Task 3"]

        result = get_next_task(Path("/test/project"))

        assert result == "Task 1"
        mock_get_incomplete.assert_called_once_with(
            str(Path("/test/project") / "pr_info"), exclude_meta_tasks=True
        )

    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_get_next_task_no_tasks(self, mock_get_incomplete: MagicMock) -> None:
        """Test getting next task when no incomplete tasks exist."""
        mock_get_incomplete.return_value = []

        result = get_next_task(Path("/test/project"))

        assert result is None
        mock_get_incomplete.assert_called_once_with(
            str(Path("/test/project") / "pr_info"), exclude_meta_tasks=True
        )

    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_get_next_task_exception(self, mock_get_incomplete: MagicMock) -> None:
        """Test getting next task handles exceptions."""
        mock_get_incomplete.side_effect = Exception("Task tracker error")

        result = get_next_task(Path("/test/project"))

        assert result is None
        mock_get_incomplete.assert_called_once_with(
            str(Path("/test/project") / "pr_info"), exclude_meta_tasks=True
        )


class TestCommitMessageFile:
    """Test commit message file handling."""

    def test_cleanup_removes_existing_file(self, tmp_path: Path) -> None:
        """Test that cleanup removes existing commit message file."""
        # Create the file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("old message")

        # Call cleanup
        _cleanup_commit_message_file(tmp_path)

        assert not commit_file.exists()

    def test_cleanup_handles_missing_file(self, tmp_path: Path) -> None:
        """Test that cleanup handles missing file gracefully."""
        # Should not raise
        _cleanup_commit_message_file(tmp_path)


class TestReadAndClearBlocked:
    """Test read_and_clear_blocked helper."""

    def test_returns_none_when_absent(self, tmp_path: Path) -> None:
        """No marker (and no pr_info/ dir) means 'not blocked'."""
        assert read_and_clear_blocked(tmp_path) is None

    def test_returns_text_and_deletes_file(self, tmp_path: Path) -> None:
        """A non-empty marker returns its text and is removed."""
        (tmp_path / "pr_info").mkdir()
        marker = tmp_path / BLOCKED_FILE
        marker.write_text("pytest times out", encoding="utf-8")

        assert read_and_clear_blocked(tmp_path) == "pytest times out"
        assert not marker.exists()

    def test_whitespace_only_returns_fallback(self, tmp_path: Path) -> None:
        """An empty marker still counts as blocked, never as 'no marker'."""
        (tmp_path / "pr_info").mkdir()
        marker = tmp_path / BLOCKED_FILE
        marker.write_text("   \n\t", encoding="utf-8")

        assert read_and_clear_blocked(tmp_path) == BLOCKED_REASON_FALLBACK
        assert not marker.exists()

    def test_long_text_truncated(self, tmp_path: Path) -> None:
        """Overlong reasons are truncated with an ellipsis marker."""
        (tmp_path / "pr_info").mkdir()
        (tmp_path / BLOCKED_FILE).write_text("x" * 900, encoding="utf-8")

        result = read_and_clear_blocked(tmp_path)

        assert result is not None
        assert len(result) == BLOCKED_REASON_MAX_CHARS + 3
        assert result.endswith("...")

    def test_blocked_file_constant(self) -> None:
        """BLOCKED_FILE is defined in the shared tier and re-exported."""
        assert BLOCKED_FILE == "pr_info/.blocked.txt"
        assert IMPLEMENT_BLOCKED_FILE is BLOCKED_FILE


class TestBlockedExitInPrompts:
    """Test that both prompt sources offer the blocked exit."""

    def test_retry_reminder_offers_blocked_exit(self) -> None:
        """The retry reminder points at the marker instead of demanding a tick."""
        assert BLOCKED_FILE in RETRY_REMINDER
        assert "you MUST tick" not in RETRY_REMINDER

    def test_implementation_prompt_offers_blocked_exit(self) -> None:
        """The attempt-1 prompt template also offers the blocked exit."""
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )

        assert BLOCKED_FILE in prompt_template


class TestCheckAndFixMypy:
    """Test check_and_fix_mypy function."""

    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_no_errors(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check when no errors found."""
        mock_mypy_check.return_value = None  # No errors

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is True
        mock_mypy_check.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_fixes_errors(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """Test mypy check fixes errors successfully."""
        # First call returns errors, second call returns None (fixed)
        mock_mypy_check.side_effect = ["mypy error output", None]
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.return_value = _make_llm_response("Fixed the errors")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is True
        assert mock_mypy_check.call_count == 2
        mock_get_prompt.assert_called_once()
        mock_prompt_llm.assert_called_once()
        # Verify store_session called with correct step_name
        mock_store_session.assert_called_once()
        call_kwargs = mock_store_session.call_args
        assert call_kwargs.kwargs.get("step_name") == "step_1_mypy_1" or (
            len(call_kwargs.args) >= 4 and call_kwargs.args[3] == "step_1_mypy_1"
        )
        assert "implement_sessions" in (
            call_kwargs.kwargs.get("store_path", "")
            or (call_kwargs.args[2] if len(call_kwargs.args) >= 3 else "")
        )

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_max_attempts(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """Test mypy check stops after max identical attempts."""
        # Always return same error (identical outputs)
        mock_mypy_check.return_value = "same mypy error"
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.return_value = _make_llm_response("Attempted fix")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False
        # Should attempt fixes until max identical attempts reached
        assert mock_prompt_llm.call_count == 3  # max_identical_attempts
        # store_session should be called once per attempt
        assert mock_store_session.call_count == 3

    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_exception(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check handles exceptions."""
        mock_mypy_check.side_effect = Exception("Mypy error")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_timeout_propagates(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Fixes the pre-existing hole: a fix-up LLMTimeoutError must propagate.

        Previously the broad handler swallowed it into a False result, hiding the
        timeout from the caller. It must now reach the caller for categorization.
        """
        from mcp_coder.llm.interface import LLMTimeoutError

        mock_mypy_check.return_value = "mypy error output"
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        with pytest.raises(LLMTimeoutError):
            check_and_fix_mypy(Path("/test/project"), 1, "claude")

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_mcp_unavailable_propagates(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """A fix-up McpServersUnavailableError must propagate, not become False."""
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )

        mock_mypy_check.return_value = "mypy error output"
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        with pytest.raises(McpServersUnavailableError):
            check_and_fix_mypy(Path("/test/project"), 1, "claude")


class TestProcessSingleTask:
    """Test process_single_task function."""

    @patch(
        "mcp_coder.workflows.implement.task_processing.RUN_MYPY_AFTER_EACH_TASK", True
    )
    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_success(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test processing single task successfully."""
        # Setup mocks
        mock_get_next_task.return_value = "Step 1: Create test file"
        mock_get_prompt.return_value = "Implementation template"
        mock_prompt_llm.return_value = _make_llm_response("LLM response")
        mock_get_status.return_value = {
            "staged": ["file1.py"],
            "modified": [],
            "untracked": [],
        }
        mock_check_mypy.return_value = True
        mock_run_formatters.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        outcome = process_single_task(
            Path("/test/project"),
            "claude",
            format_code=True,
            check_type_hints=True,
        )

        assert outcome.success is True
        assert outcome.reason == "completed"

        # Verify all steps were called
        mock_get_next_task.assert_called_once()
        mock_get_prompt.assert_called_once()
        mock_prompt_llm.assert_called_once()
        mock_get_status.assert_called_once()
        mock_check_mypy.assert_called_once()
        mock_run_formatters.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()

        # Verify store_session called with step_name="step_1"
        mock_store_session.assert_called_once()
        call_kwargs = mock_store_session.call_args
        assert call_kwargs.kwargs.get("step_name") == "step_1" or (
            len(call_kwargs.args) >= 4 and call_kwargs.args[3] == "step_1"
        )
        assert "implement_sessions" in (
            call_kwargs.kwargs.get("store_path", "")
            or (call_kwargs.args[2] if len(call_kwargs.args) >= 3 else "")
        )

    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_no_tasks(self, mock_get_next_task: MagicMock) -> None:
        """Test processing single task when no tasks available."""
        mock_get_next_task.return_value = None

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "no_tasks"

    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_prompt_error(
        self, mock_get_next_task: MagicMock, mock_get_prompt: MagicMock
    ) -> None:
        """Test processing single task with prompt loading error."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.side_effect = Exception("Prompt error")

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "error"

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_llm_error(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Test processing single task with LLM error."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = Exception("LLM error")

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "error"

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_llm_timeout(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Test processing single task returns 'timeout' on LLMTimeoutError."""
        from mcp_coder.llm.interface import LLMTimeoutError

        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = LLMTimeoutError(
            "LLM request timed out after 3600s"
        )

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "timeout"

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_llm_timeout_error(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Test that LLMTimeoutError (from any provider) is caught as timeout.

        This proves the latent bug fix: langchain timeouts now correctly
        result in 'timeout' instead of 'error'.
        """
        from mcp_coder.llm.interface import LLMTimeoutError

        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        # Simulate langchain timeout normalized by prompt_llm
        mock_prompt_llm.side_effect = LLMTimeoutError(
            "LLM request timed out after 3600s"
        )

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "timeout"

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_mcp_unavailable(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Test processing single task returns 'mcp_unavailable' on MCP failure."""
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )

        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "mcp_unavailable"

    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_no_changes(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
    ) -> None:
        """Test processing single task when no files changed."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}

        outcome = process_single_task(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "no_changes"
        # store_session still called even with no changes
        mock_store_session.assert_called_once()
        # Should not continue to formatting/commit/push when no changes

    @patch(
        "mcp_coder.workflows.implement.task_processing.RUN_MYPY_AFTER_EACH_TASK", True
    )
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_formatters_fail(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
    ) -> None:
        """Test processing single task when formatters fail."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {
            "staged": ["file.py"],
            "modified": [],
            "untracked": [],
        }
        mock_check_mypy.return_value = True
        mock_run_formatters.return_value = False

        outcome = process_single_task(
            Path("/test/project"), "claude", format_code=True, check_type_hints=True
        )

        assert outcome.success is False
        assert outcome.reason == "error"

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_attempt_appends_reminder(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """When attempt=2, the prompt passed to prompt_llm contains the retry reminder."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")

        # Force LLM error after capturing the prompt so we don't need full mocking
        # Actually, let prompt_llm succeed but then raise on get_full_status
        with patch(
            "mcp_coder.workflows.implement.task_processing.get_full_status",
            side_effect=Exception("stop here"),
        ):
            process_single_task(Path("/test/project"), "claude", attempt=2)

        # Verify the prompt passed to prompt_llm contains the reminder
        call_args = mock_prompt_llm.call_args
        prompt_sent = call_args[0][0] if call_args[0] else call_args[1]["prompt"]
        assert RETRY_REMINDER in prompt_sent

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_attempt_1_no_reminder(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """When attempt=1 (default), the prompt does NOT contain the retry reminder."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")

        with patch(
            "mcp_coder.workflows.implement.task_processing.get_full_status",
            side_effect=Exception("stop here"),
        ):
            process_single_task(Path("/test/project"), "claude", attempt=1)

        # Verify the prompt does NOT contain the reminder
        call_args = mock_prompt_llm.call_args
        prompt_sent = call_args[0][0] if call_args[0] else call_args[1]["prompt"]
        assert RETRY_REMINDER not in prompt_sent


class TestProcessSingleTaskGating:
    """Test format_code and check_type_hints gating in process_single_task."""

    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_skips_formatters_when_format_code_false(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Verify run_formatters not called when format_code=False."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {
            "staged": ["file.py"],
            "modified": [],
            "untracked": [],
        }
        mock_commit.return_value = True
        mock_push.return_value = True

        outcome = process_single_task(
            Path("/test/project"), "claude", format_code=False
        )

        assert outcome.success is True
        assert outcome.reason == "completed"
        mock_run_formatters.assert_not_called()

    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_runs_formatters_when_format_code_true(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Verify run_formatters called when format_code=True."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {
            "staged": ["file.py"],
            "modified": [],
            "untracked": [],
        }
        mock_run_formatters.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        outcome = process_single_task(Path("/test/project"), "claude", format_code=True)

        assert outcome.success is True
        assert outcome.reason == "completed"
        mock_run_formatters.assert_called_once_with(Path("/test/project"))

    @patch(
        "mcp_coder.workflows.implement.task_processing.RUN_MYPY_AFTER_EACH_TASK", True
    )
    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_skips_mypy_when_check_type_hints_false(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Verify check_and_fix_mypy not called when check_type_hints=False."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {
            "staged": ["file.py"],
            "modified": [],
            "untracked": [],
        }
        mock_commit.return_value = True
        mock_push.return_value = True

        outcome = process_single_task(
            Path("/test/project"), "claude", check_type_hints=False
        )

        assert outcome.success is True
        assert outcome.reason == "completed"
        mock_check_mypy.assert_not_called()

    @patch(
        "mcp_coder.workflows.implement.task_processing.RUN_MYPY_AFTER_EACH_TASK", True
    )
    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_runs_mypy_when_check_type_hints_true(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Verify check_and_fix_mypy called when check_type_hints=True."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {
            "staged": ["file.py"],
            "modified": [],
            "untracked": [],
        }
        mock_check_mypy.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        outcome = process_single_task(
            Path("/test/project"), "claude", check_type_hints=True
        )

        assert outcome.success is True
        assert outcome.reason == "completed"
        mock_check_mypy.assert_called_once()

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_process_task_with_retry_forwards_config_params(
        self, mock_process: MagicMock
    ) -> None:
        """Verify process_task_with_retry passes format_code and check_type_hints through."""
        mock_process.return_value = TaskOutcome(True, "completed")

        process_task_with_retry(
            Path("/test/project"),
            "claude",
            format_code=True,
            check_type_hints=True,
        )

        mock_process.assert_called_once()
        call_kwargs = mock_process.call_args
        assert call_kwargs.kwargs["format_code"] is True
        assert call_kwargs.kwargs["check_type_hints"] is True


class TestIntegration:
    """Integration tests for task processing workflow."""

    @patch(
        "mcp_coder.workflows.implement.task_processing.RUN_MYPY_AFTER_EACH_TASK", True
    )
    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.check_and_fix_mypy")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    @patch("mcp_coder.workflows.implement.task_processing.prepare_llm_environment")
    def test_full_task_processing_workflow(
        self,
        mock_prepare_env: MagicMock,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test complete task processing workflow end-to-end."""
        project_dir = Path("/test/project")

        # Setup successful workflow
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": "C:\\test\\project",
            "MCP_CODER_VENV_DIR": "C:\\Users\\Marcus\\Documents\\GitHub\\mcp_coder\\.venv",
        }
        mock_get_next_task.return_value = "Step 2: Implement feature X"
        mock_get_prompt.return_value = "Implementation Prompt: [task_info]"
        mock_prompt_llm.return_value = _make_llm_response("I'll implement feature X...")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["src/feature.py"],
            "untracked": ["tests/test_feature.py"],
        }
        mock_check_mypy.return_value = True
        mock_run_formatters.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        # Execute workflow
        outcome = process_single_task(
            project_dir, "claude", format_code=True, check_type_hints=True
        )

        # Verify success
        assert outcome.success is True
        assert outcome.reason == "completed"

        # Verify workflow steps executed in order
        mock_get_next_task.assert_called_once_with(project_dir)
        mock_get_prompt.assert_called_once()

        # Verify LLM call with correct prompt
        expected_prompt = """Implementation Prompt: [task_info]

Current task from TASK_TRACKER.md: Step 2: Implement feature X

Please implement this task step by step."""
        mock_prompt_llm.assert_called_once_with(
            expected_prompt,
            provider="claude",
            timeout=600,
            env_vars=ANY,
            execution_dir=ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=ANY,
        )

        # Verify store_session called with step_name="step_2" and implement_sessions path
        mock_store_session.assert_called_once()
        call_kwargs = mock_store_session.call_args
        assert call_kwargs.kwargs.get("step_name") == "step_2" or (
            len(call_kwargs.args) >= 4 and call_kwargs.args[3] == "step_2"
        )
        store_path = call_kwargs.kwargs.get("store_path") or (
            call_kwargs.args[2] if len(call_kwargs.args) >= 3 else ""
        )
        assert "implement_sessions" in store_path

        # Verify processing steps
        mock_get_status.assert_called_once_with(project_dir)
        mock_check_mypy.assert_called_once_with(
            project_dir, 2, "claude", ANY, None, None, None
        )
        mock_run_formatters.assert_called_once_with(project_dir)
        mock_commit.assert_called_once_with(
            project_dir,
            "claude",
            mcp_config=None,
            execution_dir=str(project_dir),
            settings_file=None,
        )
        mock_push.assert_called_once_with(project_dir)

    def test_error_recovery_patterns(self) -> None:
        """Test various error recovery scenarios."""
        project_dir = Path("/test/project")

        # Test individual function resilience
        with patch(
            "mcp_coder.workflows.implement.task_processing.get_incomplete_tasks",
            side_effect=Exception("DB error"),
        ):
            task_result = get_next_task(project_dir)
            assert task_result is None


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
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_mcp_unavailable_categorized_as_reason(
        self,
        mock_get_next_task: MagicMock,
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

        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "mcp_unavailable"
        assert mock_prompt_llm.call_count == 1


class TestProcessSingleTaskBlocked:
    """Test pr_info/.blocked.txt detection inside process_single_task."""

    @staticmethod
    def _write_marker(project_dir: Path, text: str) -> Path:
        """Create the blocked marker with the given text and return its path."""
        (project_dir / "pr_info").mkdir(exist_ok=True)
        marker = project_dir / BLOCKED_FILE
        marker.write_text(text, encoding="utf-8")
        return marker

    @classmethod
    def _llm_writes_marker(
        cls, project_dir: Path, text: str, raises: Optional[Exception] = None
    ) -> Callable[..., dict[str, object]]:
        """Build a prompt_llm side effect that drops the marker mid-call.

        The agent writes the marker during its turn, so a marker created before
        process_single_task runs would be swept by the start-of-task cleanup.
        """

        def _side_effect(*_args: Any, **_kwargs: Any) -> dict[str, object]:
            cls._write_marker(project_dir, text)
            if raises is not None:
                raise raises
            return _make_llm_response("Response")

        return _side_effect

    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_blocked_wins_over_changed_files(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A marker plus changed files is blocked, never success.

        The marker file is itself an untracked change, so if the files-changed
        check ran first the run would commit the marker and report success -
        the exact inversion this feature exists to prevent.
        """
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(
            tmp_path, "pytest never finishes"
        )
        mock_get_status.return_value = {
            "staged": ["f.py"],
            "modified": [],
            "untracked": [],
        }

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == "pytest never finishes"
        mock_commit.assert_not_called()
        mock_push.assert_not_called()
        mock_run_formatters.assert_not_called()
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_empty_marker_is_blocked_not_no_changes(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A whitespace-only marker still reports blocked, never no_changes."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(tmp_path, "   \n\t")
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == BLOCKED_REASON_FALLBACK
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_marker_plus_timeout_keeps_timeout_label(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The typed LLM failure wins the label; the marker text rides along."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(
            tmp_path,
            "mcp server never answered",
            raises=LLMTimeoutError("timed out after 3600s"),
        )

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "timeout"
        assert "mcp server never answered" in outcome.detail
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_marker_plus_mcp_unavailable_keeps_mcp_label(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Same precedence for an unavailable MCP server."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(
            tmp_path,
            "tools-py is down",
            raises=McpServersUnavailableError(
                "MCP servers unavailable",
                {"mcp-tools-py": "failed"},
            ),
        )

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "mcp_unavailable"
        assert "tools-py is down" in outcome.detail
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_stale_marker_removed_at_task_start(
        self, mock_get_next_task: MagicMock, tmp_path: Path
    ) -> None:
        """A marker left by a previous run is cleared before any work starts."""
        marker = self._write_marker(tmp_path, "left over from last run")
        mock_get_next_task.return_value = None

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "no_tasks"
        assert not marker.exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_no_marker_still_reports_no_changes(
        self,
        mock_get_next_task: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Regression guard: without a marker, behaviour is unchanged."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "no_changes"

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_blocked_does_not_retry(self, mock_process: MagicMock) -> None:
        """blocked is terminal - the retry wrapper returns it untouched."""
        mock_process.return_value = TaskOutcome(False, "blocked", "why")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == "why"
        assert mock_process.call_count == 1
