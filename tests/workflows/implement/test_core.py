"""Tests for implement workflow core orchestration.

This module tests the main workflow orchestration functions that coordinate
prerequisites checking, task tracker preparation, and task processing loops.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.core import (
    log_progress_summary,
    prepare_task_tracker,
    resolve_project_dir,
    run_implement_workflow,
)


class TestResolveProjectDir:
    """Test resolve_project_dir function."""

    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_none_uses_current_directory(self, mock_path_class: MagicMock) -> None:
        """Test resolve_project_dir uses current directory when None provided."""
        # Setup mock path instance
        mock_current_dir = MagicMock()
        mock_current_dir.exists.return_value = True
        mock_current_dir.is_dir.return_value = True
        mock_current_dir.iterdir.return_value = iter([])
        
        # Setup git directory mock
        mock_git_dir = MagicMock()
        mock_git_dir.exists.return_value = True
        mock_current_dir.__truediv__.return_value = mock_git_dir
        
        # Setup Path class mocks
        mock_path_class.cwd.return_value = mock_current_dir
        mock_current_dir.resolve.return_value = mock_current_dir
        
        # Mock Path constructor to return our mock when called with strings
        mock_path_class.return_value = mock_current_dir
        
        result = resolve_project_dir(None)
        
        assert result == mock_current_dir
        mock_path_class.cwd.assert_called_once()
        mock_current_dir.resolve.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_with_valid_path(self, mock_path_class: MagicMock) -> None:
        """Test resolve_project_dir with valid project directory path."""
        test_path = "/test/project"
        
        # Setup mock path instance
        mock_project_path = MagicMock()
        mock_project_path.exists.return_value = True
        mock_project_path.is_dir.return_value = True
        mock_project_path.iterdir.return_value = iter([])
        mock_project_path.resolve.return_value = mock_project_path
        
        # Setup git directory mock
        mock_git_dir = MagicMock()
        mock_git_dir.exists.return_value = True
        mock_project_path.__truediv__.return_value = mock_git_dir
        
        # Mock Path constructor
        mock_path_class.return_value = mock_project_path
        
        result = resolve_project_dir(test_path)
        
        assert result == mock_project_path
        mock_path_class.assert_called_once_with(test_path)
        mock_project_path.resolve.assert_called_once()

    @patch("sys.exit")
    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_invalid_path_exits(self, mock_path_class: MagicMock, mock_exit: MagicMock) -> None:
        """Test resolve_project_dir exits when path resolution fails."""
        mock_project_path = MagicMock()
        mock_project_path.resolve.side_effect = OSError("Invalid path")
        mock_path_class.return_value = mock_project_path
        
        resolve_project_dir("/invalid/path")
        
        mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_nonexistent_directory_exits(self, mock_path_class: MagicMock, mock_exit: MagicMock) -> None:
        """Test resolve_project_dir exits when directory doesn't exist."""
        mock_project_path = MagicMock()
        mock_project_path.resolve.return_value = mock_project_path
        mock_project_path.exists.return_value = False
        mock_path_class.return_value = mock_project_path
        
        resolve_project_dir("/nonexistent")
        
        mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_not_directory_exits(self, mock_path_class: MagicMock, mock_exit: MagicMock) -> None:
        """Test resolve_project_dir exits when path is not a directory."""
        mock_project_path = MagicMock()
        mock_project_path.resolve.return_value = mock_project_path
        mock_project_path.exists.return_value = True
        mock_project_path.is_dir.return_value = False
        mock_path_class.return_value = mock_project_path
        
        resolve_project_dir("/test/file.txt")
        
        mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_no_git_directory_exits(self, mock_path_class: MagicMock, mock_exit: MagicMock) -> None:
        """Test resolve_project_dir exits when .git directory doesn't exist."""
        mock_project_path = MagicMock()
        mock_project_path.resolve.return_value = mock_project_path
        mock_project_path.exists.return_value = True
        mock_project_path.is_dir.return_value = True
        mock_project_path.iterdir.return_value = iter([])
        
        # Setup git directory mock that doesn't exist
        mock_git_dir = MagicMock()
        mock_git_dir.exists.return_value = False
        mock_project_path.__truediv__.return_value = mock_git_dir
        
        mock_path_class.return_value = mock_project_path
        
        resolve_project_dir("/test/project")
        
        mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("mcp_coder.workflows.implement.core.Path")
    def test_resolve_project_dir_permission_error_exits(self, mock_path_class: MagicMock, mock_exit: MagicMock) -> None:
        """Test resolve_project_dir exits when directory is not accessible."""
        mock_project_path = MagicMock()
        mock_project_path.resolve.return_value = mock_project_path
        mock_project_path.exists.return_value = True
        mock_project_path.is_dir.return_value = True
        mock_project_path.iterdir.side_effect = PermissionError("Access denied")
        mock_path_class.return_value = mock_project_path
        
        resolve_project_dir("/test/project")
        
        mock_exit.assert_called_once_with(1)


class TestPrepareTaskTracker:
    """Test prepare_task_tracker function."""

    def test_prepare_task_tracker_already_has_tasks(self) -> None:
        """Test prepare_task_tracker skips when tasks already exist."""
        project_dir = Path("/test/project")
        
        # Mock the Path operations that might be causing issues
        with (
            patch("mcp_coder.workflows.implement.core.has_implementation_tasks", return_value=True) as mock_has_tasks,
            patch.object(Path, "__truediv__") as mock_div,
            patch.object(Path, "exists", return_value=True)
        ):
            # Setup the path division mock for pr_info/steps
            mock_steps_dir = MagicMock()
            mock_steps_dir.exists.return_value = True
            mock_div.return_value = mock_steps_dir
            
            result = prepare_task_tracker(project_dir, "claude_code_cli")

            assert result is True
            mock_has_tasks.assert_called_once_with(project_dir)

    def test_prepare_task_tracker_no_steps_directory(self) -> None:
        """Test prepare_task_tracker fails when steps directory doesn't exist."""
        project_dir = Path("/test/project")
        
        with (
            patch.object(Path, "__truediv__") as mock_div,
        ):
            # Setup the path division mock for pr_info/steps - directory doesn't exist
            mock_steps_dir = MagicMock()
            mock_steps_dir.exists.return_value = False
            mock_div.return_value = mock_steps_dir
            
            result = prepare_task_tracker(project_dir, "claude_code_cli")

        assert result is False

    def test_prepare_task_tracker_success(self) -> None:
        """Test prepare_task_tracker successfully updates task tracker."""
        project_dir = Path("/test/project")
        
        with (
            patch("mcp_coder.workflows.implement.core.get_prompt") as mock_get_prompt,
            patch("mcp_coder.workflows.implement.core.parse_llm_method") as mock_parse_llm,
            patch("mcp_coder.workflows.implement.core.ask_llm") as mock_ask_llm,
            patch("mcp_coder.workflows.implement.core.get_full_status") as mock_get_status,
            patch("mcp_coder.workflows.implement.core.has_implementation_tasks") as mock_has_tasks,
            patch("mcp_coder.workflows.implement.core.commit_all_changes") as mock_commit,
            patch.object(Path, "__truediv__") as mock_div,
        ):
            # Setup: no tasks initially, then has tasks after update
            mock_has_tasks.side_effect = [False, True]
            mock_get_prompt.return_value = "Task tracker update prompt"
            mock_parse_llm.return_value = ("claude", "cli")
            mock_ask_llm.return_value = "Updated task tracker content"
            mock_get_status.return_value = {
                "staged": [],
                "modified": ["pr_info/TASK_TRACKER.md"],
                "untracked": [],
            }
            mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
            
            # Setup the path division mock for pr_info/steps - directory exists
            mock_steps_dir = MagicMock()
            mock_steps_dir.exists.return_value = True
            mock_div.return_value = mock_steps_dir
            
            result = prepare_task_tracker(project_dir, "claude_code_cli")

            assert result is True
            mock_get_prompt.assert_called_once()
            mock_ask_llm.assert_called_once()
            mock_commit.assert_called_once()

    @patch("mcp_coder.workflows.implement.prerequisites.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.parse_llm_method")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    def test_prepare_task_tracker_llm_error(
        self,
        mock_get_prompt: MagicMock,
        mock_parse_llm: MagicMock,
        mock_ask_llm: MagicMock,
        mock_has_tasks: MagicMock,
    ) -> None:
        """Test prepare_task_tracker handles LLM errors."""
        mock_has_tasks.return_value = False
        mock_get_prompt.return_value = "Prompt"
        mock_parse_llm.return_value = ("claude", "cli")
        mock_ask_llm.return_value = None  # Empty response

        with patch.object(Path, "exists", return_value=True):
            result = prepare_task_tracker(Path("/test/project"), "claude_code_cli")

        assert result is False

    @patch("mcp_coder.workflows.implement.prerequisites.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.parse_llm_method")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    def test_prepare_task_tracker_unexpected_files_modified(
        self,
        mock_get_prompt: MagicMock,
        mock_parse_llm: MagicMock,
        mock_ask_llm: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
    ) -> None:
        """Test prepare_task_tracker fails when unexpected files are modified."""
        mock_has_tasks.return_value = False
        mock_get_prompt.return_value = "Prompt"
        mock_parse_llm.return_value = ("claude", "cli")
        mock_ask_llm.return_value = "Response"
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["unexpected_file.py", "pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }

        with patch.object(Path, "exists", return_value=True):
            result = prepare_task_tracker(Path("/test/project"), "claude_code_cli")

        assert result is False

    @patch("mcp_coder.workflows.implement.prerequisites.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.parse_llm_method")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    def test_prepare_task_tracker_still_no_tasks_after_update(
        self,
        mock_get_prompt: MagicMock,
        mock_parse_llm: MagicMock,
        mock_ask_llm: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
    ) -> None:
        """Test prepare_task_tracker fails when still no tasks after LLM update."""
        # Always returns False - no tasks before or after
        mock_has_tasks.return_value = False
        mock_get_prompt.return_value = "Prompt"
        mock_parse_llm.return_value = ("claude", "cli")
        mock_ask_llm.return_value = "Response"
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }

        with patch.object(Path, "exists", return_value=True):
            result = prepare_task_tracker(Path("/test/project"), "claude_code_cli")

        assert result is False

    @patch("mcp_coder.workflows.implement.core.commit_all_changes")
    @patch("mcp_coder.workflows.implement.prerequisites.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.core.get_full_status")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.parse_llm_method")
    @patch("mcp_coder.workflows.implement.core.get_prompt")
    def test_prepare_task_tracker_commit_fails(
        self,
        mock_get_prompt: MagicMock,
        mock_parse_llm: MagicMock,
        mock_ask_llm: MagicMock,
        mock_get_status: MagicMock,
        mock_has_tasks: MagicMock,
        mock_commit: MagicMock,
    ) -> None:
        """Test prepare_task_tracker handles commit failures."""
        mock_has_tasks.side_effect = [False, True]
        mock_get_prompt.return_value = "Prompt"
        mock_parse_llm.return_value = ("claude", "cli")
        mock_ask_llm.return_value = "Response"
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": False, "error": "Commit failed"}

        with patch.object(Path, "exists", return_value=True):
            result = prepare_task_tracker(Path("/test/project"), "claude_code_cli")

        assert result is False


class TestLogProgressSummary:
    """Test log_progress_summary function."""

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_success(self, mock_get_progress: MagicMock) -> None:
        """Test log_progress_summary with valid progress data."""
        mock_get_progress.return_value = {
            "Step 1": {
                "total": 5,
                "completed": 3,
                "incomplete": 2,
                "incomplete_tasks": ["Task A", "Task B"],
            },
            "Step 2": {
                "total": 3,
                "completed": 3,
                "incomplete": 0,
                "incomplete_tasks": [],
            },
        }

        # Should not raise any exceptions
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_no_progress(
        self, mock_get_progress: MagicMock
    ) -> None:
        """Test log_progress_summary when no progress data available."""
        mock_get_progress.return_value = None

        # Should not raise any exceptions
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_empty_progress(
        self, mock_get_progress: MagicMock
    ) -> None:
        """Test log_progress_summary with empty progress data."""
        mock_get_progress.return_value = {}

        # Should not raise any exceptions
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_exception(self, mock_get_progress: MagicMock) -> None:
        """Test log_progress_summary handles exceptions gracefully."""
        mock_get_progress.side_effect = Exception("Progress error")

        # Should not raise exceptions - handles errors gracefully
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    def test_log_progress_summary_with_many_incomplete_tasks(
        self, mock_get_progress: MagicMock
    ) -> None:
        """Test log_progress_summary truncates long incomplete task lists."""
        mock_get_progress.return_value = {
            "Step 1": {
                "total": 10,
                "completed": 5,
                "incomplete": 5,
                "incomplete_tasks": [
                    "Task A",
                    "Task B",
                    "Task C",
                    "Task D",
                    "Task E",
                    "Task F",
                ],
            }
        }

        # Should not raise any exceptions and should handle long lists
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )


class TestRunImplementWorkflow:
    """Test run_implement_workflow function."""

    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_success_no_tasks(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_process_task: MagicMock,
        mock_log_progress: MagicMock,
    ) -> None:
        """Test run_implement_workflow with successful prerequisites but no tasks."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.return_value = (False, "no_tasks")

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 0  # Success exit code
        mock_check_git.assert_called_once()
        mock_check_branch.assert_called_once()
        mock_check_prereq.assert_called_once()
        mock_prepare_tracker.assert_called_once()
        mock_process_task.assert_called_once()
        assert mock_log_progress.call_count == 1  # Final only

    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_git_check_fails(
        self, mock_check_git: MagicMock
    ) -> None:
        """Test run_implement_workflow fails early on git check."""
        mock_check_git.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 1  # Error exit code
        mock_check_git.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_branch_check_fails(
        self, mock_check_git: MagicMock, mock_check_branch: MagicMock
    ) -> None:
        """Test run_implement_workflow fails on branch check."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 1  # Error exit code
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
        """Test run_implement_workflow fails on prerequisites check."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 1  # Error exit code
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
        """Test run_implement_workflow fails on task tracker preparation."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = False

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 1  # Error exit code
        mock_prepare_tracker.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
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
        mock_process_task: MagicMock,
        mock_log_progress: MagicMock,
    ) -> None:
        """Test run_implement_workflow handles task processing errors."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.return_value = (False, "error")

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 1  # Error exit code
        mock_process_task.assert_called_once()
        # Should still call progress summary even on error
        assert mock_log_progress.call_count >= 1

    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_multiple_tasks(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_process_task: MagicMock,
        mock_log_progress: MagicMock,
    ) -> None:
        """Test run_implement_workflow processes multiple tasks successfully."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        # First 3 calls succeed, 4th call indicates no more tasks
        mock_process_task.side_effect = [
            (True, "completed"),
            (True, "completed"),
            (True, "completed"),
            (False, "no_tasks"),
        ]

        result = run_implement_workflow(Path("/test/project"), "claude_code_cli")

        assert result == 0  # Success exit code
        assert mock_process_task.call_count == 4  # 3 tasks + 1 no_tasks check
        # Initial progress + progress after each task + final progress
        assert mock_log_progress.call_count == 5


class TestIntegration:
    """Integration tests for core workflow orchestration."""

    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_full_workflow_orchestration_success(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_process_task: MagicMock,
        mock_log_progress: MagicMock,
    ) -> None:
        """Test complete workflow orchestration end-to-end."""
        project_dir = Path("/test/project")
        llm_method = "claude_code_api"

        # Setup successful workflow
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True

        # Simulate processing 2 tasks then completion
        mock_process_task.side_effect = [
            (True, "completed"),  # Task 1
            (True, "completed"),  # Task 2
            (False, "no_tasks"),  # No more tasks
        ]

        # Execute full workflow
        result = run_implement_workflow(project_dir, llm_method)

        # Verify success
        assert result == 0

        # Verify all phases executed in order
        mock_check_git.assert_called_once_with(project_dir)
        mock_check_branch.assert_called_once_with(project_dir)
        mock_check_prereq.assert_called_once_with(project_dir)
        mock_prepare_tracker.assert_called_once_with(project_dir, llm_method)

        # Verify task processing loop
        assert mock_process_task.call_count == 3
        for call in mock_process_task.call_args_list:
            assert call[0] == (project_dir, llm_method)

        # Verify progress tracking
        assert mock_log_progress.call_count == 4  # Initial + after each task + final

    def test_workflow_failure_scenarios(self) -> None:
        """Test various workflow failure scenarios and error handling."""
        project_dir = Path("/test/project")
        llm_method = "claude_code_cli"

        # Test early failure scenarios
        with patch(
            "mcp_coder.workflows.implement.core.check_git_clean", return_value=False
        ):
            result = run_implement_workflow(project_dir, llm_method)
            assert result == 1

        with (
            patch(
                "mcp_coder.workflows.implement.core.check_git_clean", return_value=True
            ),
            patch(
                "mcp_coder.workflows.implement.core.check_main_branch",
                return_value=False,
            ),
        ):
            result = run_implement_workflow(project_dir, llm_method)
            assert result == 1

        with (
            patch(
                "mcp_coder.workflows.implement.core.check_git_clean", return_value=True
            ),
            patch(
                "mcp_coder.workflows.implement.core.check_main_branch", return_value=True
            ),
            patch(
                "mcp_coder.workflows.implement.core.check_prerequisites",
                return_value=False,
            ),
        ):
            result = run_implement_workflow(project_dir, llm_method)
            assert result == 1

    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_progress_tracking_pattern(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_process_task: MagicMock,
        mock_log_progress: MagicMock,
    ) -> None:
        """Test workflow progress tracking pattern with various task counts."""
        project_dir = Path("/test/project")
        llm_method = "claude_code_cli"

        # Setup successful prerequisites
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True

        # Test with 5 successful tasks
        task_results = [(True, "completed")] * 5 + [(False, "no_tasks")]
        mock_process_task.side_effect = task_results

        result = run_implement_workflow(project_dir, llm_method)

        assert result == 0
        assert mock_process_task.call_count == 6  # 5 tasks + no_tasks check

        # Progress should be called:
        # 1 initial + 5 after each task + 1 final = 7 times
        assert mock_log_progress.call_count == 7

        # Verify progress was called with correct project_dir
        for call in mock_log_progress.call_args_list:
            assert call[0] == (project_dir,)

    def test_error_resilience_and_logging(self) -> None:
        """Test workflow error resilience and logging behavior."""
        project_dir = Path("/test/project")
        llm_method = "claude_code_cli"

        # Test exception handling in resolve_project_dir
        with (
            patch("mcp_coder.workflows.implement.core.Path") as mock_path_class,
            patch("sys.exit") as mock_exit,
        ):
            mock_project_path = MagicMock()
            mock_project_path.resolve.side_effect = ValueError("Invalid path format")
            mock_path_class.return_value = mock_project_path
            
            resolve_project_dir("/invalid")
            mock_exit.assert_called_once_with(1)

        # Test exception handling in log_progress_summary
        with patch(
            "mcp_coder.workflows.implement.core.get_step_progress",
            side_effect=Exception("Progress read error"),
        ):
            # Should not raise - should handle gracefully
            log_progress_summary(project_dir)

        # Test exception handling in prepare_task_tracker
        with (
            patch.object(Path, "exists", return_value=True),
            patch(
                "mcp_coder.workflows.implement.prerequisites.has_implementation_tasks",
                return_value=False,
            ),
            patch(
                "mcp_coder.workflows.implement.core.get_prompt",
                side_effect=Exception("Prompt loading error"),
            ),
        ):
            result = prepare_task_tracker(project_dir, llm_method)
            assert result is False