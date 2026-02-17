"""Tests for implement workflow core orchestration."""

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_utils.task_tracker import TaskTrackerFileNotFoundError
from mcp_coder.workflows.implement.core import (
    _get_rebase_target_branch,
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
        "method": "cli",
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
        result = prepare_task_tracker(tmp_path, "claude", "cli")
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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")

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
        result = prepare_task_tracker(tmp_path, "claude", "cli")

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

        run_implement_workflow(Path("/test"), "claude", "cli")

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

        run_implement_workflow(Path("/test"), "claude", "cli")

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

        run_implement_workflow(Path("/test"), "claude", "cli")

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
        result = prepare_task_tracker(tmp_path, "claude", "cli", execution_dir=exec_dir)

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
        result = prepare_task_tracker(tmp_path, "claude", "cli", execution_dir=None)

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_finalisation(tmp_path, "claude", "cli")

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
        result = run_finalisation(tmp_path, "claude", "cli")

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

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

        assert result == 0
        mock_check_git.assert_called_once()
        mock_check_branch.assert_called_once()
        mock_check_prereq.assert_called_once()
        # Verify prepare_task_tracker was called with None for execution_dir
        mock_prepare_tracker.assert_called_once_with(
            Path("/test/project"), "claude", "cli", None, None
        )
        assert mock_process_task.call_count == 2
        # Verify process_task was called with None for execution_dir
        first_call_args = mock_process_task.call_args_list[0][0]
        assert first_call_args == (Path("/test/project"), "claude", "cli", None, None)
        assert mock_log_progress.call_count >= 2  # Initial + final progress

    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_git_not_clean(
        self, mock_check_git: MagicMock
    ) -> None:
        """Test run_implement_workflow when git is not clean."""
        mock_check_git.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

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

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

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

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

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

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

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

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

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

        result = run_implement_workflow(Path("/test/project"), "claude", "cli")

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

        result = run_implement_workflow(tmp_path, "claude", "cli")

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

        result = prepare_task_tracker(tmp_path, "claude", "cli")
        assert result is False

        # Test progress logging without data
        log_progress_summary(tmp_path)  # Should not raise exception
