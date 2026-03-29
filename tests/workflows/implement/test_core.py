"""Tests for implement workflow core orchestration."""

import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_utils.task_tracker import TaskTrackerFileNotFoundError
from mcp_coder.workflows.implement.constants import FailureCategory, WorkflowFailure
from mcp_coder.workflows.implement.core import (
    _format_elapsed_time,
    _format_failure_comment,
    _get_diff_stat,
    _get_rebase_target_branch,
    _handle_workflow_failure,
    _poll_for_ci_completion,
    log_progress_summary,
    prepare_task_tracker,
    run_finalisation,
    run_implement_workflow,
)
from mcp_coder.workflows.utils import resolve_project_dir


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


class TestResolveProjectDir:
    """Test resolve_project_dir function."""

    def test_resolve_project_dir_none_uses_cwd(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with None uses current working directory."""
        # Create .git directory in temp path
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = resolve_project_dir(None)
            assert result == tmp_path

    def test_resolve_project_dir_with_valid_path(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with valid project directory."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = resolve_project_dir(str(tmp_path))
        assert result == tmp_path

    def test_resolve_project_dir_invalid_path_raises_value_error(self) -> None:
        """Test resolve_project_dir with invalid path raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            resolve_project_dir("/invalid/nonexistent/path")

    def test_resolve_project_dir_not_directory_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir with non-directory path raises ValueError."""
        # Create a file instead of directory
        test_file = tmp_path / "test_file"
        test_file.write_text("test content")

        with pytest.raises(ValueError, match="not a directory"):
            resolve_project_dir(str(test_file))

    def test_resolve_project_dir_no_git_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir without .git directory raises ValueError."""
        with pytest.raises(ValueError, match="not a git repository"):
            resolve_project_dir(str(tmp_path))

    def test_resolve_project_dir_permission_error_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir with permission error raises ValueError."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock permission error during directory listing
        with patch.object(
            Path, "iterdir", side_effect=PermissionError("Access denied")
        ):
            with pytest.raises(ValueError, match="No read access"):
                resolve_project_dir(str(tmp_path))

    def test_resolve_project_dir_resolve_error_raises_value_error(self) -> None:
        """Test resolve_project_dir with path resolve error raises ValueError."""
        # Mock OSError during path resolution
        with patch.object(Path, "resolve", side_effect=OSError("Path error")):
            with pytest.raises(ValueError, match="Invalid project directory path"):
                resolve_project_dir("/some/path")


class TestPrepareTaskTracker:
    """Test prepare_task_tracker function."""

    def test_prepare_task_tracker_no_steps_dir(self, tmp_path: Path) -> None:
        """Test prepare_task_tracker when steps directory doesn't exist."""
        result = prepare_task_tracker(tmp_path, "claude")
        assert result is False

    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
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

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.get_prompt")
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

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
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

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_exception(self, mock_get_progress: MagicMock) -> None:
        """Test log_progress_summary handles exceptions gracefully."""
        mock_get_progress.side_effect = Exception("Progress error")

        # Should not raise an exception
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )


class TestGetRebaseTargetBranch:
    """Tests for _get_rebase_target_branch function."""

    @patch("mcp_coder.workflows.implement.core.detect_base_branch")
    def test_returns_pr_base_branch(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns base_branch when detect_base_branch finds a valid branch."""
        mock_detect_base.return_value = "develop"

        result = _get_rebase_target_branch(tmp_path)
        assert result == "develop"

    @patch("mcp_coder.workflows.implement.core.detect_base_branch")
    def test_returns_none_when_detection_fails(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns None when detect_base_branch returns None."""
        mock_detect_base.return_value = None

        result = _get_rebase_target_branch(tmp_path)
        assert result is None

    @patch("mcp_coder.workflows.implement.core.detect_base_branch")
    def test_returns_valid_branch_from_detection(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns the branch name when detect_base_branch returns a valid branch."""
        mock_detect_base.return_value = "main"

        result = _get_rebase_target_branch(tmp_path)
        assert result == "main"


class TestRebaseIntegration:
    """Tests for rebase integration in workflow."""

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_and_push_called_after_prerequisites(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test rebase is attempted after prerequisites pass."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = True  # Push succeeds

        run_implement_workflow(Path("/test"), "claude")

        mock_get_target.assert_called_once()
        mock_rebase.assert_called_once_with(Path("/test"), "main")

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_push_with_force_with_lease_after_successful_rebase(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test push is called with force_with_lease=True after successful rebase."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = True  # Push succeeds

        run_implement_workflow(Path("/test"), "claude")

        # Verify push was called with force_with_lease=True
        mock_push.assert_called_once_with(Path("/test"), force_with_lease=True)

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_rebase_fails(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test workflow continues even when rebase returns False."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop workflow here to focus on rebase
        mock_get_target.return_value = "main"
        mock_rebase.return_value = False  # Rebase failed

        # Should not fail - workflow continues past rebase failure
        result = run_implement_workflow(Path("/test"), "claude", "cli")

        # Workflow should have continued to prepare_task_tracker
        mock_prepare.assert_called_once()
        # Push should not be called when rebase fails
        mock_push.assert_not_called()
        # Result is 1 because prepare_task_tracker returns False, not because of rebase
        assert result == 1

    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_skipped_when_no_target_branch(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
    ) -> None:
        """Test rebase is skipped when target branch cannot be detected."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = False  # Stop here
        mock_get_target.return_value = None  # No target detected

        run_implement_workflow(Path("/test"), "claude")

        mock_rebase.assert_not_called()

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_push_after_rebase_fails(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test workflow continues even when push after rebase fails."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop workflow here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = False  # Push fails

        # Should not fail - workflow continues past push failure
        result = run_implement_workflow(Path("/test"), "claude", "cli")

        # Workflow should have continued to prepare_task_tracker
        mock_prepare.assert_called_once()
        # Result is 1 because prepare_task_tracker returns False
        assert result == 1


class TestPrepareTaskTrackerExecutionDir:
    """Test execution_dir parameter in prepare_task_tracker."""

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
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


class TestRunFinalisation:
    """Tests for run_finalisation function."""

    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_skips_when_no_incomplete_tasks(
        self, mock_has_incomplete: MagicMock, tmp_path: Path
    ) -> None:
        """Test run_finalisation skips LLM call when no incomplete tasks."""
        mock_has_incomplete.return_value = False

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_has_incomplete.assert_called_once_with(str(tmp_path / "pr_info"))

    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_calls_llm_when_incomplete_tasks(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation calls LLM when there are incomplete tasks."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        # No changes after LLM call
        mock_get_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_prompt_llm.assert_called_once()
        # Verify the prompt contains key finalisation instructions
        call_args = mock_prompt_llm.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get("question", "")
        assert "TASK_TRACKER.md" in prompt
        assert "unchecked tasks" in prompt
        # Verify store_session called with finalisation step_name
        mock_store_session.assert_called_once()
        store_call_kwargs = mock_store_session.call_args[1]
        assert store_call_kwargs.get("step_name") == "finalisation"

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_commits_and_pushes_when_changes_exist(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation commits and pushes changes when they exist."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = True

        # Create commit message file
        pr_info_dir = tmp_path / "pr_info"
        pr_info_dir.mkdir(parents=True)
        commit_msg_file = pr_info_dir / ".commit_message.txt"
        commit_msg_file.write_text("Test commit message")

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_commit.assert_called_once_with("Test commit message", tmp_path)
        mock_push.assert_called_once_with(tmp_path)
        # Verify commit message file was deleted
        assert not commit_msg_file.exists()

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.generate_commit_message_with_llm")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_uses_llm_generated_message_when_file_missing(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_generate_commit_msg: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation uses LLM-generated message when commit file missing."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        # LLM generates commit message successfully
        mock_generate_commit_msg.return_value = (
            True,
            "LLM generated commit message",
            None,
        )
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = True

        # Don't create commit message file - should fall back to LLM

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_generate_commit_msg.assert_called_once()
        mock_commit.assert_called_once_with("LLM generated commit message", tmp_path)
        mock_push.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.generate_commit_message_with_llm")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_uses_default_message_when_llm_fails(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_generate_commit_msg: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation uses default message when both file and LLM fail."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        # LLM fails to generate commit message
        mock_generate_commit_msg.return_value = (False, "", "LLM error")
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = True

        # Don't create commit message file - LLM also fails - should use default

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_generate_commit_msg.assert_called_once()
        mock_commit.assert_called_once_with(
            "Finalisation: complete remaining tasks", tmp_path
        )
        mock_push.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_no_commit_when_no_changes(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation skips commit when no changes after LLM."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        # No commit or push should be called

    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_returns_false_when_task_tracker_missing(
        self, mock_has_incomplete: MagicMock, tmp_path: Path
    ) -> None:
        """Test run_finalisation returns False when task tracker is missing."""
        mock_has_incomplete.side_effect = TaskTrackerFileNotFoundError(
            "TASK_TRACKER.md not found"
        )

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_returns_false_on_empty_llm_response(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation returns False when LLM returns empty response."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("")  # Empty text

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_returns_false_when_commit_fails(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation returns False when commit fails."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": False, "error": "Commit failed"}

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_returns_false_when_push_fails(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation returns False when push fails."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = False

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.has_incomplete_work")
    def test_run_finalisation_store_session_failure_is_non_critical(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation succeeds even when store_session raises."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_store_session.side_effect = Exception("Storage failure")
        mock_get_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        # Should still succeed even though store_session raises
        result = run_finalisation(tmp_path, "claude")

        assert result is True


class TestRunImplementWorkflow:
    """Test run_implement_workflow function."""

    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_success(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
    ) -> None:
        """Test run_implement_workflow successful execution."""
        # Setup mocks for success path
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        # First call: success, second call: no tasks (completion)
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 0
        mock_check_git.assert_called_once()
        mock_check_branch.assert_called_once()
        mock_check_prereq.assert_called_once()
        # Verify prepare_task_tracker was called with None for execution_dir
        mock_prepare_tracker.assert_called_once_with(
            Path("/test/project"), "claude", None, None
        )
        assert mock_process_task.call_count == 2
        # Verify process_task was called with None for execution_dir
        first_call_args = mock_process_task.call_args_list[0][0]
        assert first_call_args == (Path("/test/project"), "claude", None, None)
        assert mock_log_progress.call_count >= 2  # Initial + final progress

    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_git_not_clean(
        self, mock_check_git: MagicMock
    ) -> None:
        """Test run_implement_workflow when git is not clean."""
        mock_check_git.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_check_git.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_on_main_branch(
        self, mock_check_git: MagicMock, mock_check_branch: MagicMock
    ) -> None:
        """Test run_implement_workflow when on main branch."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_check_git.assert_called_once()
        mock_check_branch.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_prerequisites_fail(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
    ) -> None:
        """Test run_implement_workflow when prerequisites fail."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_check_git.assert_called_once()
        mock_check_branch.assert_called_once()
        mock_check_prereq.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_task_tracker_preparation_fails(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
    ) -> None:
        """Test run_implement_workflow when task tracker preparation fails."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_prepare_tracker.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_task_processing_error(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
    ) -> None:
        """Test run_implement_workflow when task processing fails."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.return_value = (False, "error")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_process_task.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_no_tasks_initially(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
    ) -> None:
        """Test run_implement_workflow when no tasks exist initially."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.return_value = (False, "no_tasks")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 0  # Should succeed with no tasks
        mock_process_task.assert_called_once()


class TestIntegration:
    """Integration tests for core workflow orchestration."""

    @pytest.mark.skipif(
        sys.platform.startswith("linux"),
        reason="Log capture behaves differently on Linux",
    )
    @patch("mcp_coder.workflows.implement.core.RUN_MYPY_AFTER_EACH_TASK", True)
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.store_session")
    @patch("mcp_coder.workflows.implement.core.prompt_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_full_workflow_success(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
        mock_get_progress: MagicMock,
        mock_process_task: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test complete workflow execution from start to finish."""
        # Create steps directory for prepare_task_tracker
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        # Setup prerequisite checks
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True

        # Setup task tracker preparation
        mock_has_tasks.side_effect = [False, True]  # First no tasks, then has tasks
        mock_prepare_env.return_value = {
            "MCP_CODER_PROJECT_DIR": str(tmp_path),
            "MCP_CODER_VENV_DIR": str(tmp_path / ".venv"),
        }
        mock_get_prompt.return_value = "Task tracker update prompt"
        mock_prompt_llm.return_value = _make_llm_response("LLM updated task tracker")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        # Setup progress tracking
        mock_get_progress.return_value = {
            "Step 1": {
                "total": 2,
                "completed": 1,
                "incomplete": 1,
                "incomplete_tasks": ["Task 1"],
            }
        }

        # Setup task processing - complete one task then finish
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]

        result = run_implement_workflow(tmp_path, "claude")

        # Verify successful completion
        assert result == 0

        # Verify all workflow phases executed
        mock_check_git.assert_called_once_with(tmp_path)
        mock_check_branch.assert_called_once_with(tmp_path)
        mock_check_prereq.assert_called_once_with(tmp_path)

        # Verify task tracker was prepared
        assert mock_has_tasks.call_count == 2
        mock_get_prompt.assert_called_once()
        mock_prompt_llm.assert_called_once()
        mock_commit.assert_called_once()

        # Verify task processing
        assert mock_process_task.call_count == 2

    def test_resolve_project_dir_real_filesystem(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with real filesystem operations."""
        # Create a valid git repository structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Test with absolute path (skip relative path test since tmp_path may not be under cwd)
        result = resolve_project_dir(str(tmp_path))
        assert result == tmp_path

    def test_error_recovery_workflow(self, tmp_path: Path) -> None:
        """Test workflow behavior during various error conditions."""
        # Test without .git directory
        with pytest.raises(ValueError, match="not a git repository"):
            resolve_project_dir(str(tmp_path))

        # Test with .git directory but no steps
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = prepare_task_tracker(tmp_path, "claude")
        assert result is False

        # Test progress logging without data
        log_progress_summary(tmp_path)  # Should not raise exception


class TestGetDiffStat:
    """Tests for _get_diff_stat."""

    @patch("mcp_coder.workflows.implement.core._safe_repo_context")
    def test_returns_diff_stat(self, mock_ctx: MagicMock) -> None:
        """Returns git diff --stat output."""
        mock_repo = MagicMock()
        mock_repo.git.diff.return_value = "file.py | 3 +++"
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_repo)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = _get_diff_stat(Path("/project"))

        assert result == "file.py | 3 +++"
        mock_repo.git.diff.assert_called_once_with("HEAD", "--stat")

    @patch("mcp_coder.workflows.implement.core._safe_repo_context")
    def test_returns_empty_on_error(self, mock_ctx: MagicMock) -> None:
        """Returns empty string when git fails."""
        mock_ctx.side_effect = Exception("git error")

        result = _get_diff_stat(Path("/project"))

        assert result == ""


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

    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_sets_failure_label(
        self,
        mock_diff: MagicMock,
        mock_issue_cls: MagicMock,
        mock_branch: MagicMock,
    ) -> None:
        """Failure handler sets the correct label."""
        mock_diff.return_value = ""
        mock_branch.return_value = None
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="failed",
        )
        _handle_workflow_failure(failure, Path("/project"))

        mock_manager.update_workflow_label.assert_called_once_with(
            from_label_id="implementing",
            to_label_id="implementing_failed",
        )

    @patch("mcp_coder.workflows.implement.core.extract_issue_number_from_branch")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_posts_github_comment(
        self,
        mock_diff: MagicMock,
        mock_issue_cls: MagicMock,
        mock_branch: MagicMock,
        mock_extract: MagicMock,
    ) -> None:
        """Failure handler posts comment with failure details."""
        mock_branch.return_value = "189-feature"
        mock_extract.return_value = 189
        mock_diff.return_value = "file.py | 3 +++"
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="Task implementation",
            message="timed out",
            tasks_completed=2,
            tasks_total=5,
        )
        _handle_workflow_failure(failure, Path("/project"))

        mock_manager.add_comment.assert_called_once()
        comment = mock_manager.add_comment.call_args[0][1]
        assert "Implementation Failed" in comment
        assert "Llm Timeout" in comment
        assert "2/5" in comment
        assert "file.py" in comment

    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_label_error_non_blocking(
        self,
        mock_diff: MagicMock,
        mock_issue_cls: MagicMock,
        mock_branch: MagicMock,
    ) -> None:
        """Label update failure should not raise."""
        mock_diff.return_value = ""
        mock_branch.return_value = None
        mock_manager = MagicMock()
        mock_manager.update_workflow_label.side_effect = Exception("API error")
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="failed",
        )
        # Should not raise
        _handle_workflow_failure(failure, Path("/project"))

    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_ci_exhaustion_sets_ci_fix_needed_label(
        self,
        mock_diff: MagicMock,
        mock_issue_cls: MagicMock,
        mock_branch: MagicMock,
    ) -> None:
        """CI fix exhaustion sets ci_fix_needed label."""
        mock_diff.return_value = ""
        mock_branch.return_value = None
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.CI_FIX_EXHAUSTED,
            stage="CI pipeline fix",
            message="CI failed",
        )
        _handle_workflow_failure(failure, Path("/project"))

        mock_manager.update_workflow_label.assert_called_once_with(
            from_label_id="implementing",
            to_label_id="ci_fix_needed",
        )

    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_timeout_sets_llm_timeout_label(
        self,
        mock_diff: MagicMock,
        mock_issue_cls: MagicMock,
        mock_branch: MagicMock,
    ) -> None:
        """LLM timeout sets llm_timeout label."""
        mock_diff.return_value = ""
        mock_branch.return_value = None
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="Task implementation",
            message="timed out",
        )
        _handle_workflow_failure(failure, Path("/project"))

        mock_manager.update_workflow_label.assert_called_once_with(
            from_label_id="implementing",
            to_label_id="llm_timeout",
        )


class TestRunImplementWorkflowLabelTransitions:
    """Test that labels always transition on success/failure."""

    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_success_always_updates_label_to_code_review(
        self,
        mock_branch: MagicMock,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_process: MagicMock,
        mock_progress: MagicMock,
        mock_finalise: MagicMock,
        mock_ci: MagicMock,
        mock_issue_cls: MagicMock,
    ) -> None:
        """On success, label transitions to code_review unconditionally."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "no_tasks")
        mock_finalise.return_value = True
        mock_branch.return_value = "189-feature"
        mock_ci.return_value = True
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 0
        mock_manager.update_workflow_label.assert_called_once_with(
            from_label_id="implementing",
            to_label_id="code_review",
        )

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_prerequisite_failures_dont_change_labels(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Prerequisite failures return 1 without calling failure handler."""
        mock_git_clean.return_value = False

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_not_called()

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
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
        """When LLM times out, calls _handle_workflow_failure with LLM_TIMEOUT."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "timeout")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.LLM_TIMEOUT
        assert failure_arg.stage == "Task implementation"

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
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
        """When task errors, calls _handle_workflow_failure with GENERAL."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "error")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.GENERAL
        assert failure_arg.stage == "Task implementation"


class TestNoPostErrorProgressDisplay:
    """Verify post-error progress display is removed."""

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_no_progress_summary_after_error(
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
        """After error, log_progress_summary is only called once (initial), not after error."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "error")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        # log_progress_summary called once for initial display (Step 3)
        # NOT called again after error (post-error display removed)
        mock_progress.assert_called_once()
        mock_handle_failure.assert_called_once()


class TestFormatElapsedTime:
    """Tests for _format_elapsed_time."""

    def test_seconds_only(self) -> None:
        """Formats sub-minute durations as seconds only."""
        assert _format_elapsed_time(45.7) == "45s"

    def test_minutes_and_seconds(self) -> None:
        """Formats durations with minutes and seconds."""
        assert _format_elapsed_time(754.0) == "12m 34s"

    def test_hours_minutes_seconds(self) -> None:
        """Formats durations with hours, minutes, and seconds."""
        assert _format_elapsed_time(3661.0) == "1h 1m 1s"

    def test_zero(self) -> None:
        """Formats zero seconds."""
        assert _format_elapsed_time(0.0) == "0s"


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
    @patch("mcp_coder.workflows.implement.core.process_single_task")
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
        mock_finalisation: MagicMock,
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
    @patch("mcp_coder.workflows.implement.core.process_single_task")
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
        mock_finalisation: MagicMock,
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
    @patch("mcp_coder.workflows.implement.core.process_single_task")
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
        mock_finalisation: MagicMock,
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


class TestWorkflowSafetyNet:
    """Tests for the try/finally safety net in run_implement_workflow."""

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker",
        side_effect=RuntimeError("unexpected"),
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_safety_net_fires_on_unexpected_exception(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """Safety net fires on unexpected exception to post GitHub comment and set label."""
        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 1
        mock_handle.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feat-123",
    )
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.process_single_task",
        return_value=(False, "no_tasks"),
    )
    @patch("mcp_coder.workflows.implement.core.get_step_progress", return_value={})
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=True)
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_safety_net_does_not_fire_on_normal_success(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_progress: MagicMock,
        mock_step_progress: MagicMock,
        mock_process: MagicMock,
        mock_finalisation: MagicMock,
        mock_branch: MagicMock,
        mock_ci: MagicMock,
        mock_issue_mgr: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """Safety net does NOT fire when workflow completes successfully."""
        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 0
        unexpected_calls = [
            c for c in mock_handle.call_args_list if c[0][0].stage == "Unexpected exit"
        ]
        assert len(unexpected_calls) == 0

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_safety_net_does_not_double_handle(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """When workflow already handled a failure, safety net does not fire again."""
        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 1
        assert mock_handle.call_count == 1
        assert mock_handle.call_args[0][0].stage == "Task tracker preparation"

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker",
        side_effect=RuntimeError("boom"),
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    @patch.dict(os.environ, {"BUILD_URL": "https://jenkins.example.com/job/1/console"})
    def test_caught_exception_triggers_safety_net(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """Unexpected exception allows safety net to fire for GitHub reporting."""
        result = run_implement_workflow(Path("/fake"), "claude")

        assert result == 1
        mock_handle.assert_called_once()


class TestSigtermHandler:
    """Tests for SIGTERM handler registration and behavior."""

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_sigterm_handler_registered(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """SIGTERM handler is registered after prereq checks pass."""
        run_implement_workflow(Path("/fake"), "claude")

        sigterm_calls = [
            c for c in mock_signal.call_args_list if c[0][0] == signal.SIGTERM
        ]
        assert len(sigterm_calls) >= 1

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_sigterm_handler_restored_in_finally(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """Previous SIGTERM handler is restored after workflow completes."""
        original_handler = MagicMock()
        mock_signal.return_value = original_handler

        run_implement_workflow(Path("/fake"), "claude")

        final_call = mock_signal.call_args_list[-1]
        assert final_call[0][0] == signal.SIGTERM
        assert final_call[0][1] == original_handler

    @patch("mcp_coder.workflows.implement.core.signal.signal")
    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_sigterm_sets_flag_and_exits(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prep: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """SIGTERM handler sets sigterm_received flag and calls sys.exit(1)."""
        # Capture the registered handler
        handlers: dict[int, Any] = {}

        def capture_handler(sig: int, handler: Any) -> Any:
            handlers[sig] = handler
            return signal.SIG_DFL

        mock_signal.side_effect = capture_handler

        # Make prepare_task_tracker call the SIGTERM handler
        def trigger_sigterm(*args: Any, **kwargs: Any) -> None:
            handler = handlers.get(signal.SIGTERM)
            if handler:
                with pytest.raises(SystemExit):
                    handler(signal.SIGTERM, None)
            raise SystemExit(1)

        mock_prep.side_effect = trigger_sigterm

        with pytest.raises(SystemExit):
            run_implement_workflow(Path("/fake"), "claude")

        # The finally block should have called _handle_workflow_failure
        # with stage "SIGTERM received"
        mock_handle.assert_called()
        failure = mock_handle.call_args[0][0]
        assert failure.stage == "SIGTERM received"
        assert failure.message == "Workflow terminated by signal"


class TestPollForCiCompletionHeartbeat:
    """Tests for elapsed time and heartbeat logging in _poll_for_ci_completion."""

    def test_heartbeat_logged_at_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """INFO heartbeat is logged every 8 iterations."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        # 9 in-progress responses, then completed on 10th
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 9 + [
            completed
        ]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.INFO):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 1  # Fires at iteration 8

    def test_no_heartbeat_before_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No heartbeat logged when fewer than 8 iterations complete."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        # Only 5 in-progress, then completed
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 5 + [
            completed
        ]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.INFO):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 0

    def test_elapsed_time_in_debug_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress, completed]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.DEBUG):
                _poll_for_ci_completion(mock_ci_manager, "main")

        debug_logs = [
            r
            for r in caplog.records
            if "elapsed" in r.message.lower() and "in progress" in r.message.lower()
        ]
        assert len(debug_logs) >= 1

    def test_elapsed_time_in_no_run_found_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """'No CI run found yet' debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        empty_status: Dict[str, Any] = {"run": {}, "jobs": []}
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [empty_status, completed]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.DEBUG):
                _poll_for_ci_completion(mock_ci_manager, "main")

        no_run_logs = [
            r
            for r in caplog.records
            if "no ci run found" in r.message.lower() and "elapsed" in r.message.lower()
        ]
        assert len(no_run_logs) >= 1

    def test_multiple_heartbeats_at_16_iterations(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Two heartbeats logged at iterations 8 and 16."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 17 + [
            completed
        ]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.INFO):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 2  # Fires at iterations 8 and 16
