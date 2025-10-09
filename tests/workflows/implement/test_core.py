"""Tests for implement workflow core orchestration."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.core import (
    log_progress_summary,
    prepare_task_tracker,
    run_implement_workflow,
)
from mcp_coder.workflows.utils import resolve_project_dir


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

    def test_resolve_project_dir_invalid_path_exits(self) -> None:
        """Test resolve_project_dir with invalid path exits with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir("/invalid/nonexistent/path")
        assert exc_info.value.code == 1

    def test_resolve_project_dir_not_directory_exits(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with non-directory path exits with code 1."""
        # Create a file instead of directory
        test_file = tmp_path / "test_file"
        test_file.write_text("test content")

        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(test_file))
        assert exc_info.value.code == 1

    def test_resolve_project_dir_no_git_exits(self, tmp_path: Path) -> None:
        """Test resolve_project_dir without .git directory exits with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(tmp_path))
        assert exc_info.value.code == 1

    def test_resolve_project_dir_permission_error_exits(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with permission error exits with code 1."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock permission error during directory listing
        with patch.object(
            Path, "iterdir", side_effect=PermissionError("Access denied")
        ):
            with pytest.raises(SystemExit) as exc_info:
                resolve_project_dir(str(tmp_path))
            assert exc_info.value.code == 1

    def test_resolve_project_dir_resolve_error_exits(self) -> None:
        """Test resolve_project_dir with path resolve error exits with code 1."""
        # Mock OSError during path resolution
        with patch.object(Path, "resolve", side_effect=OSError("Path error")):
            with pytest.raises(SystemExit) as exc_info:
                resolve_project_dir("/some/path")
            assert exc_info.value.code == 1


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
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    def test_prepare_task_tracker_success(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_ask_llm: MagicMock,
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
        mock_ask_llm.return_value = "LLM updated the task tracker"
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
        # No longer need to parse LLM method - using structured parameters
        mock_ask_llm.assert_called_once()
        mock_get_status.assert_called_once_with(tmp_path)
        mock_commit.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    def test_prepare_task_tracker_empty_llm_response(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_ask_llm: MagicMock,
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
        mock_ask_llm.return_value = ""  # Empty response

        result = prepare_task_tracker(tmp_path, "claude", "cli")

        assert result is False

    @patch("mcp_coder.workflows.implement.core.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    def test_prepare_task_tracker_unexpected_files_changed(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_ask_llm: MagicMock,
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
        mock_ask_llm.return_value = "LLM response"
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
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    def test_prepare_task_tracker_still_no_tasks_after_update(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_ask_llm: MagicMock,
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
        mock_ask_llm.return_value = "LLM response"
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
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    @patch("mcp_coder.workflows.implement.core.prepare_llm_environment")
    def test_prepare_task_tracker_commit_fails(
        self,
        mock_prepare_env: MagicMock,
        mock_get_prompt: MagicMock,
        mock_ask_llm: MagicMock,
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
        mock_ask_llm.return_value = "LLM response"
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

    @pytest.mark.skipif(
        sys.platform.startswith("linux"),
        reason="Log capture behaves differently on Linux",
    )
    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_with_progress(
        self, mock_get_progress: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test log_progress_summary with progress data."""
        mock_get_progress.return_value = {
            "Step 1": {
                "total": 5,
                "completed": 3,
                "incomplete": 2,
                "incomplete_tasks": ["Task 1", "Task 2"],
            },
            "Step 2": {
                "total": 3,
                "completed": 3,
                "incomplete": 0,
                "incomplete_tasks": [],
            },
        }

        with caplog.at_level("INFO"):
            log_progress_summary(Path("/test/project"))

        # Use caplog.records for pytest-xdist compatibility (more reliable than caplog.text)
        log_messages = [record.message for record in caplog.records]
        all_logs = " ".join(log_messages)

        # Check that progress information was logged
        assert any("TASK TRACKER PROGRESS SUMMARY" in msg for msg in log_messages)
        assert any("Step 1:" in msg for msg in log_messages)
        assert any("Step 2:" in msg for msg in log_messages)
        assert "60%" in all_logs  # 3/5 = 60%
        assert "100%" in all_logs  # 3/3 = 100%
        assert "Task 1, Task 2" in all_logs  # Incomplete tasks listed

    @pytest.mark.skipif(
        sys.platform.startswith("linux"),
        reason="Log capture behaves differently on Linux",
    )
    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_zero_total_tasks(
        self, mock_get_progress: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test log_progress_summary with zero total tasks."""
        mock_get_progress.return_value = {
            "Step 1": {
                "total": 0,
                "completed": 0,
                "incomplete": 0,
                "incomplete_tasks": [],
            }
        }

        with caplog.at_level("INFO"):
            log_progress_summary(Path("/test/project"))

        # Use caplog.records for pytest-xdist compatibility
        all_logs = " ".join(record.message for record in caplog.records)

        assert "0%" in all_logs  # 0/0 should show 0%

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_exception(self, mock_get_progress: MagicMock) -> None:
        """Test log_progress_summary handles exceptions gracefully."""
        mock_get_progress.side_effect = Exception("Progress error")

        # Should not raise an exception
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )


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
        mock_prepare_tracker.assert_called_once()
        assert mock_process_task.call_count == 2
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

    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_multiple_tasks_then_error(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run_implement_workflow processes multiple tasks then encounters error."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        # Success, success, then error
        mock_process_task.side_effect = [
            (True, "completed"),
            (True, "completed"),
            (False, "error"),
        ]

        with caplog.at_level("INFO"):
            result = run_implement_workflow(Path("/test/project"), "claude", "cli")
            # Capture log text inside context manager for pytest-xdist compatibility
            log_text = caplog.text

        assert result == 1
        assert mock_process_task.call_count == 3
        # Check that workflow error was logged (ERROR message is reliably captured on all platforms)
        assert "Task processing failed - stopping workflow" in log_text


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
    @patch("mcp_coder.workflows.implement.core.ask_llm")
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
        mock_ask_llm: MagicMock,
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
        mock_ask_llm.return_value = "LLM updated task tracker"
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
        mock_ask_llm.assert_called_once()
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
        with pytest.raises(SystemExit):
            resolve_project_dir(str(tmp_path))

        # Test with .git directory but no steps
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = prepare_task_tracker(tmp_path, "claude", "cli")
        assert result is False

        # Test progress logging without data
        log_progress_summary(tmp_path)  # Should not raise exception
