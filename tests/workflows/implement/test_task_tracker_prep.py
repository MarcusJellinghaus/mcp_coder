"""Tests for implement workflow task tracker preparation."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.task_tracker_prep import (
    log_progress_summary,
    prepare_task_tracker,
)


# Reusable LLMResponseDict mock value
def _make_llm_response(text: str = "LLM response text") -> Dict[str, Any]:
    return {
        "text": text,
        "session_id": "test-session",
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


class TestPrepareTaskTracker:
    """Test prepare_task_tracker function."""

    def test_prepare_task_tracker_no_steps_dir(self, tmp_path: Path) -> None:
        """Test prepare_task_tracker when steps directory doesn't exist."""
        result = prepare_task_tracker(tmp_path, "claude")
        assert result is False

    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    def test_prepare_task_tracker_already_has_tasks(
        self, mock_has_tasks: MagicMock, tmp_path: Path
    ) -> None:
        """Test prepare_task_tracker when tracker already has tasks."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_has_tasks.return_value = True

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is True
        mock_has_tasks.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_success(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker successful execution."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        # Setup mocks
        mock_has_tasks.side_effect = [
            False,
            True,
        ]  # First call: no tasks, second: has tasks
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response(
            "LLM updated the task tracker"
        )
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is True
        assert mock_has_tasks.call_count == 2
        mock_get_prompt.assert_called_once()
        mock_prompt_llm.assert_called_once()
        # Verify execution_dir parameter is passed as None by default
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs.get("execution_dir") is None
        mock_get_status.assert_called_once_with(tmp_path)
        mock_commit.assert_called_once()
        # Verify store_session called with task_tracker step_name
        mock_store_session.assert_called_once()
        store_call_kwargs = mock_store_session.call_args[1]
        assert store_call_kwargs.get("step_name") == "task_tracker"
        assert "implement_sessions" in store_call_kwargs.get("store_path", "")

    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_empty_llm_response(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker with empty LLM response."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_has_tasks.return_value = False
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response("")  # Empty text response

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_unexpected_files_changed(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker when unexpected files are changed."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_has_tasks.return_value = False
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response("LLM response")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md", "src/unexpected_file.py"],
            "untracked": [],
        }

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_still_no_tasks_after_update(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker when task tracker still has no tasks after update."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_has_tasks.return_value = False  # Always returns False
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response("LLM response")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_commit_fails(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker when commit fails."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_has_tasks.side_effect = [False, True]
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response("LLM response")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": False, "error": "Commit failed"}

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    def test_prepare_task_tracker_exception(
        self, mock_get_prompt: MagicMock, tmp_path: Path
    ) -> None:
        """Test prepare_task_tracker handles exceptions."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_get_prompt.side_effect = Exception("Prompt loading error")

        result = prepare_task_tracker(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_ignores_uv_lock(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker ignores uv.lock in changed files.

        When uv.lock is modified alongside TASK_TRACKER.md, the function should
        succeed because uv.lock is in DEFAULT_IGNORED_BUILD_ARTIFACTS.
        """
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        # Setup mocks
        mock_has_tasks.side_effect = [False, True]
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response(
            "LLM updated the task tracker"
        )
        # uv.lock is also modified - should be ignored
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": ["uv.lock"],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        result = prepare_task_tracker(tmp_path, "claude")

        # Should succeed - uv.lock should be filtered out
        assert result is True
        mock_commit.assert_called_once()

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_prepare_task_tracker_store_session_failure_is_non_critical(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prepare_task_tracker succeeds even when store_session raises."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        mock_has_tasks.side_effect = [False, True]
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response(
            "LLM updated the task tracker"
        )
        mock_store_session.side_effect = Exception("Storage failure")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        # Should still succeed even though store_session raises
        result = prepare_task_tracker(tmp_path, "claude")

        assert result is True
        mock_commit.assert_called_once()


class TestLogProgressSummary:
    """Test log_progress_summary function."""

    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_step_progress")
    def test_log_progress_summary_no_progress(
        self, mock_get_progress: MagicMock
    ) -> None:
        """Test log_progress_summary when no progress information available."""
        mock_get_progress.return_value = None

        # Should not raise an exception
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_step_progress")
    def test_log_progress_summary_exception(self, mock_get_progress: MagicMock) -> None:
        """Test log_progress_summary handles exceptions gracefully."""
        mock_get_progress.side_effect = Exception("Progress error")

        # Should not raise an exception
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )


class TestPrepareTaskTrackerExecutionDir:
    """Test execution_dir parameter in prepare_task_tracker."""

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_execution_dir_passed_to_prompt_llm(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test execution_dir is passed to prompt_llm call."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        # Setup mocks
        mock_has_tasks.side_effect = [False, True]
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response(
            "LLM updated the task tracker"
        )
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        # Create execution_dir
        exec_dir = tmp_path / "execution"
        exec_dir.mkdir()

        # Call with execution_dir
        result = prepare_task_tracker(tmp_path, "claude", execution_dir=exec_dir)

        assert result is True
        # Verify execution_dir was passed to prompt_llm
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs.get("execution_dir") == str(exec_dir)

    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
    def test_execution_dir_none_uses_default(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test execution_dir=None passes None to prompt_llm."""
        # Create steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        # Setup mocks
        mock_has_tasks.side_effect = [False, True]
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response(
            "LLM updated the task tracker"
        )
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        # Call with execution_dir=None (default)
        result = prepare_task_tracker(tmp_path, "claude", execution_dir=None)

        assert result is True
        # Verify execution_dir was passed as None
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs.get("execution_dir") is None
