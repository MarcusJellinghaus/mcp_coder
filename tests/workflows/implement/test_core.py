"""Tests for implement workflow core orchestration."""

import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_utils.task_tracker import TaskTrackerFileNotFoundError
from mcp_coder.workflows.implement.constants import FailureCategory, WorkflowFailure
from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_tracker_prep import (
    log_progress_summary,
    prepare_task_tracker,
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


class TestRunImplementWorkflow:
    """Test run_implement_workflow function."""

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
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
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
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
            Path("/test/project"), "claude", None, None, None
        )
        assert mock_process_task.call_count == 2
        # Verify process_task was called with None for execution_dir
        first_call_args = mock_process_task.call_args_list[0][0]
        assert first_call_args == (Path("/test/project"), "claude", None, None, None)
        # Verify config booleans passed (defaults from missing pyproject.toml)
        first_call_kwargs = mock_process_task.call_args_list[0][1]
        assert first_call_kwargs["format_code"] is False
        assert first_call_kwargs["check_type_hints"] is False
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

    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
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

    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
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

    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_reads_config(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_config: MagicMock,
    ) -> None:
        """Test that get_implement_config is called with project_dir."""
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.return_value = (False, "no_tasks")

        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=False, check_type_hints=False
        )

        run_implement_workflow(Path("/test/project"), "claude")

        mock_get_config.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_passes_config_to_process_task(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
    ) -> None:
        """Test that config booleans are passed to process_task_with_retry."""
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=True, check_type_hints=True
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]

        run_implement_workflow(Path("/test/project"), "claude")

        first_call_kwargs = mock_process_task.call_args_list[0][1]
        assert first_call_kwargs["format_code"] is True
        assert first_call_kwargs["check_type_hints"] is True

    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_skips_final_mypy_when_disabled(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
    ) -> None:
        """Test that check_type_hints=False skips final mypy in Step 5."""
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=True, check_type_hints=False
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 0
        mock_check_mypy.assert_not_called()

    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_run_implement_workflow_skips_final_formatting_when_disabled(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
    ) -> None:
        """Test that format_code=False skips formatters in Step 5 while mypy still runs."""
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=False, check_type_hints=True
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 0
        # mypy should still be called since check_type_hints=True
        mock_check_mypy.assert_called_once()
        # but formatters should NOT be called since format_code=False
        mock_run_formatters.assert_not_called()

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_final_mypy_timeout_categorized_as_llm_timeout(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """A final-mypy LLMTimeoutError is categorized to LLM_TIMEOUT (was swallowed)."""
        from mcp_coder.llm.interface import LLMTimeoutError
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=False, check_type_hints=True
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]
        mock_check_mypy.side_effect = LLMTimeoutError("timed out")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.LLM_TIMEOUT
        assert failure_arg.stage == "Final mypy check"

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy")
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_final_mypy_mcp_unavailable_categorized_as_mcp_unavailable(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """A final-mypy McpServersUnavailableError is categorized to MCP_UNAVAILABLE."""
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=False, check_type_hints=True
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]
        mock_check_mypy.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.MCP_UNAVAILABLE
        assert failure_arg.stage == "Final mypy check"

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_ci_analysis_timeout_categorized_as_llm_timeout(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """A CI-analysis LLMTimeoutError propagates and is categorized to LLM_TIMEOUT."""
        from mcp_coder.llm.interface import LLMTimeoutError
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=False, check_type_hints=True
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]
        mock_check_ci.side_effect = LLMTimeoutError("timed out")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.LLM_TIMEOUT
        assert failure_arg.stage == "CI pipeline analysis"

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.get_implement_config")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
    @patch("mcp_coder.workflows.implement.core.run_formatters", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_llm_environment", return_value={}
    )
    @patch(
        "mcp_coder.workflows.implement.core.get_current_branch_name",
        return_value="feature/test-branch",
    )
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_ci_analysis_mcp_unavailable_categorized_as_mcp_unavailable(
        self,
        mock_check_git: MagicMock,
        mock_check_branch: MagicMock,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        mock_get_branch: MagicMock,
        mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        mock_run_formatters: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        mock_check_ci: MagicMock,
        mock_get_config: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """A CI-analysis McpServersUnavailableError is categorized to MCP_UNAVAILABLE."""
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(
            format_code=False, check_type_hints=True
        )
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]
        mock_check_ci.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.MCP_UNAVAILABLE
        assert failure_arg.stage == "CI pipeline analysis"


class TestIntegration:
    """Integration tests for core workflow orchestration."""

    @pytest.mark.skipif(
        sys.platform.startswith("linux"),
        reason="Log capture behaves differently on Linux",
    )
    @patch("mcp_coder.workflows.implement.core.RUN_MYPY_AFTER_EACH_TASK", True)
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.get_step_progress")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.commit_all_changes")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.has_implementation_tasks")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_full_status")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.store_session")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.get_prompt")
    @patch("mcp_coder.workflows.implement.task_tracker_prep.prepare_llm_environment")
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


class TestRunImplementWorkflowLabelTransitions:
    """Test that labels always transition on success/failure."""

    @patch("mcp_coder.workflows.implement.core.update_workflow_label")
    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_success_updates_label_when_update_issue_labels_enabled(
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
        mock_update_label: MagicMock,
    ) -> None:
        """On success with update_issue_labels=True, label transitions to code_review."""
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

        result = run_implement_workflow(
            Path("/project"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_update_label.assert_called_once_with(
            mock_manager,
            from_label_id="implementing",
            to_label_id="code_review",
        )

    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_success_skips_label_when_update_issue_labels_disabled(
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
        """On success with update_issue_labels=False, label is not updated."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "no_tasks")
        mock_finalise.return_value = True
        mock_branch.return_value = "189-feature"
        mock_ci.return_value = True

        result = run_implement_workflow(
            Path("/project"), "claude", update_issue_labels=False
        )

        assert result == 0
        mock_issue_cls.assert_not_called()

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
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
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
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_mcp_unavailable_calls_handle_failure_with_mcp_unavailable(
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
        """reason 'mcp_unavailable' routes to MCP_UNAVAILABLE failure handling."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "mcp_unavailable")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.MCP_UNAVAILABLE
        assert failure_arg.stage == "Task implementation"

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_no_changes_after_retries_routes_to_failure(
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
        """No changes after retries routes to NO_CHANGES_AFTER_RETRIES failure."""
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereq.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "no_changes_after_retries")

        result = run_implement_workflow(Path("/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[0][0]
        assert failure_arg.category == FailureCategory.NO_CHANGES_AFTER_RETRIES
        assert failure_arg.stage == "Task implementation"

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
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
    @patch("mcp_coder.workflows.implement.core.process_task_with_retry")
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
        "mcp_coder.workflows.implement.core.process_task_with_retry",
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
        _mock_step_progress: MagicMock,
        mock_process: MagicMock,
        _mock_finalisation: MagicMock,
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
