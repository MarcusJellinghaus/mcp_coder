"""Tests for implement workflow task processing."""

from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

from mcp_coder.workflows.implement.task_processing import (
    _cleanup_commit_message_file,
    check_and_fix_mypy,
    commit_changes,
    get_next_task,
    process_single_task,
    push_changes,
    run_formatters,
)


def _make_llm_response(text: str = "LLM response") -> dict:
    """Create a minimal LLMResponseDict-compatible dict for mocking."""
    return {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": text,
        "session_id": "test-session-id",
        "method": "api",
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


class TestRunFormatters:
    """Test run_formatters function."""

    @patch("mcp_coder.workflows.implement.task_processing.format_code")
    def test_run_formatters_success(self, mock_format_code: MagicMock) -> None:
        """Test running formatters successfully."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_format_code.return_value = {"black": mock_result, "isort": mock_result}

        result = run_formatters(Path("/test/project"))

        assert result is True
        mock_format_code.assert_called_once_with(
            Path("/test/project"), formatters=["black", "isort"]
        )

    @patch("mcp_coder.workflows.implement.task_processing.format_code")
    def test_run_formatters_failure(self, mock_format_code: MagicMock) -> None:
        """Test running formatters with failure."""
        mock_success_result = MagicMock()
        mock_success_result.success = True

        mock_failed_result = MagicMock()
        mock_failed_result.success = False
        mock_failed_result.error_message = "Black formatting failed"

        mock_format_code.return_value = {
            "black": mock_failed_result,
            "isort": mock_success_result,
        }

        result = run_formatters(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.format_code")
    def test_run_formatters_exception(self, mock_format_code: MagicMock) -> None:
        """Test running formatters with exception."""
        mock_format_code.side_effect = Exception("Formatter error")

        result = run_formatters(Path("/test/project"))

        assert result is False


class TestCommitChanges:
    """Test commit_changes function."""

    @patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_uses_file_when_present(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit_changes uses prepared file instead of LLM."""
        # Create commit message file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("feat: prepared message\n\nBody text here.")

        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(tmp_path)

        assert result is True
        # LLM should NOT be called
        mock_generate_message.assert_not_called()
        # File should be deleted
        assert not commit_file.exists()
        # Commit should use the prepared message
        mock_commit.assert_called_once()
        call_args = mock_commit.call_args[0]
        assert "feat: prepared message" in call_args[0]

    @patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_falls_back_to_llm_when_no_file(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit_changes falls back to LLM when file doesn't exist."""
        mock_generate_message.return_value = (True, "feat: llm message", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(tmp_path)

        assert result is True
        mock_generate_message.assert_called_once()

    @patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_deletes_empty_file_and_falls_back_to_llm(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit_changes deletes empty file and falls back to LLM."""
        # Create empty commit message file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("   \n  ")  # Whitespace only

        mock_generate_message.return_value = (True, "feat: llm message", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(tmp_path)

        assert result is True
        # File should be deleted even though it was empty
        assert not commit_file.exists()
        # LLM should be called as fallback
        mock_generate_message.assert_called_once()

    @patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_success(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test committing changes successfully."""
        mock_generate_message.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(Path("/test/project"))

        assert result is True
        mock_generate_message.assert_called_once_with(
            Path("/test/project"), "claude", "api"
        )
        mock_commit.assert_called_once_with(
            "feat: add new feature", Path("/test/project")
        )

    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_message_generation_fails(
        self, mock_generate_message: MagicMock
    ) -> None:
        """Test committing changes when message generation fails."""
        mock_generate_message.return_value = (False, None, "LLM error")

        result = commit_changes(Path("/test/project"))

        assert result is False
        mock_generate_message.assert_called_once_with(
            Path("/test/project"), "claude", "api"
        )

    @patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_commit_fails(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test committing changes when commit operation fails."""
        mock_generate_message.return_value = (True, "feat: add feature", None)
        mock_commit.return_value = {
            "success": False,
            "commit_hash": None,
            "error": "Git commit failed",
        }

        result = commit_changes(Path("/test/project"))

        assert result is False

    @patch(
        "mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm"
    )
    def test_commit_changes_exception(self, mock_generate_message: MagicMock) -> None:
        """Test committing changes with exception."""
        mock_generate_message.side_effect = Exception("Commit error")

        result = commit_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
    def test_commit_changes_logs_message_on_failure(
        self, mock_commit: MagicMock, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test commit message is logged when commit fails."""
        # Create commit message file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("feat: important message")

        mock_commit.return_value = {
            "success": False,
            "commit_hash": None,
            "error": "Git failed",
        }

        result = commit_changes(tmp_path)

        assert result is False
        # Message should be logged so it's not lost
        assert "feat: important message" in caplog.text


class TestPushChanges:
    """Test push_changes function."""

    @patch("mcp_coder.workflows.implement.task_processing.git_push")
    def test_push_changes_success(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes successfully."""
        mock_git_push.return_value = {"success": True, "error": None}

        result = push_changes(Path("/test/project"))

        assert result is True
        mock_git_push.assert_called_once_with(
            Path("/test/project"), force_with_lease=False
        )

    @patch("mcp_coder.workflows.implement.task_processing.git_push")
    def test_push_changes_failure(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes with failure."""
        mock_git_push.return_value = {
            "success": False,
            "error": "Remote repository not accessible",
        }

        result = push_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.git_push")
    def test_push_changes_exception(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes with exception."""
        mock_git_push.side_effect = Exception("Push error")

        result = push_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.git_push")
    def test_push_changes_with_force_with_lease(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes with force_with_lease=True."""
        mock_git_push.return_value = {"success": True, "error": None}

        result = push_changes(Path("/test/project"), force_with_lease=True)

        assert result is True
        mock_git_push.assert_called_once_with(
            Path("/test/project"), force_with_lease=True
        )

    @patch("mcp_coder.workflows.implement.task_processing.git_push")
    def test_push_changes_force_with_lease_failure(
        self, mock_git_push: MagicMock
    ) -> None:
        """Test force push with lease when remote has new commits."""
        mock_git_push.return_value = {
            "success": False,
            "error": "failed to push some refs: stale info",
        }

        result = push_changes(Path("/test/project"), force_with_lease=True)

        assert result is False
        mock_git_push.assert_called_once_with(
            Path("/test/project"), force_with_lease=True
        )


class TestCheckAndFixMypy:
    """Test check_and_fix_mypy function."""

    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_no_errors(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check when no errors found."""
        mock_mypy_check.return_value = None  # No errors

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude", "cli")

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

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude", "api")

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

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude", "cli")

        assert result is False
        # Should attempt fixes until max identical attempts reached
        assert mock_prompt_llm.call_count == 3  # max_identical_attempts
        # store_session should be called once per attempt
        assert mock_store_session.call_count == 3

    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_exception(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check handles exceptions."""
        mock_mypy_check.side_effect = Exception("Mypy error")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude", "cli")

        assert result is False


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

        success, reason = process_single_task(Path("/test/project"), "claude", "api")

        assert success is True
        assert reason == "completed"

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

        success, reason = process_single_task(Path("/test/project"), "claude", "cli")

        assert success is False
        assert reason == "no_tasks"

    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_next_task")
    def test_process_single_task_prompt_error(
        self, mock_get_next_task: MagicMock, mock_get_prompt: MagicMock
    ) -> None:
        """Test processing single task with prompt loading error."""
        mock_get_next_task.return_value = "Step 1: Test task"
        mock_get_prompt.side_effect = Exception("Prompt error")

        success, reason = process_single_task(Path("/test/project"), "claude", "cli")

        assert success is False
        assert reason == "error"

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

        success, reason = process_single_task(Path("/test/project"), "claude", "cli")

        assert success is False
        assert reason == "error"

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

        success, reason = process_single_task(Path("/test/project"), "claude", "cli")

        assert success is True
        assert reason == "completed"
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

        success, reason = process_single_task(Path("/test/project"), "claude", "cli")

        assert success is False
        assert reason == "error"


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
        success, reason = process_single_task(project_dir, "claude", "api")

        # Verify success
        assert success is True
        assert reason == "completed"

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
            method="api",
            timeout=3600,
            env_vars=ANY,
            execution_dir=ANY,
            mcp_config=None,
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
            project_dir, 2, "claude", "api", ANY, None, None
        )
        mock_run_formatters.assert_called_once_with(project_dir)
        mock_commit.assert_called_once_with(project_dir, "claude", "api")
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

        with patch(
            "mcp_coder.workflows.implement.task_processing.format_code",
            side_effect=Exception("Format error"),
        ):
            format_result = run_formatters(project_dir)
            assert format_result is False

        with patch(
            "mcp_coder.workflows.implement.task_processing.git_push",
            side_effect=Exception("Network error"),
        ):
            push_result = push_changes(project_dir)
            assert push_result is False
