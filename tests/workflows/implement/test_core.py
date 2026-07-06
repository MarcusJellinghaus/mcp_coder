"""Tests for implement workflow core orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.constants import FailureCategory
from mcp_coder.workflows.implement.core import run_implement_workflow


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
