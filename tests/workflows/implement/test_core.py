"""Tests for implement workflow core orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_processing import TaskOutcome


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
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 0
        mock_check_git.assert_called_once()
        mock_check_branch.assert_called_once()
        mock_check_prereq.assert_called_once()
        mock_prepare_tracker.assert_called_once_with(
            Path("/test/project"), "claude", None, None
        )
        assert mock_process_task.call_count == 2
        first_call_args = mock_process_task.call_args_list[0][0]
        assert first_call_args == (Path("/test/project"), "claude", None, None)
        # Verify config booleans passed (defaults from missing pyproject.toml)
        first_call_kwargs = mock_process_task.call_args_list[0][1]
        assert "format_code" not in first_call_kwargs
        assert first_call_kwargs["check_type_hints"] is True
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

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
    @patch(
        "mcp_coder.workflows.implement.core.check_formatter_config",
        return_value="No formatter configured",
    )
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_formatter_config_error_fails_before_task_tracker(
        self,
        _mock_check_git: MagicMock,
        _mock_check_branch: MagicMock,
        _mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_check_formatter: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """A formatter config error fails as general before any LLM call."""
        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_check_formatter.assert_called_once_with(
            Path("/test/project"), warn_legacy_key=True
        )
        mock_prepare_tracker.assert_not_called()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "implementing_failed"
        assert failure_arg.stage == "Formatter configuration"
        assert failure_arg.message == "No formatter configured"

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
        mock_process_task.return_value = TaskOutcome(False, "error")

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
        mock_process_task.return_value = TaskOutcome(False, "no_tasks")

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
        mock_process_task.return_value = TaskOutcome(False, "no_tasks")

        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(check_type_hints=False)

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

        mock_get_config.return_value = ImplementConfig(check_type_hints=True)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]

        run_implement_workflow(Path("/test/project"), "claude")

        first_call_kwargs = mock_process_task.call_args_list[0][1]
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

        mock_get_config.return_value = ImplementConfig(check_type_hints=False)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]

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
    @patch("mcp_coder.workflows.implement.core.read_and_clear_blocked")
    def test_final_mypy_clears_marker_and_formats(
        self,
        mock_read_blocked: MagicMock,
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
        """Formatters always run (gate is inside them); marker cleared before staging."""
        from mcp_coder.utils.pyproject_config import ImplementConfig

        mock_get_config.return_value = ImplementConfig(check_type_hints=True)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]
        # Order the two calls relative to each other: a marker written by the
        # final-mypy LLM turns must be gone before get_full_status stages.
        manager = MagicMock()
        manager.attach_mock(mock_read_blocked, "read_blocked")
        manager.attach_mock(mock_get_status, "get_status")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 0
        # mypy should still be called since check_type_hints=True
        mock_check_mypy.assert_called_once()
        # run_formatters owns the format_code gate, so it is always called
        mock_run_formatters.assert_called_once_with(Path("/test/project"))
        call_names = [name for name, _, _ in manager.mock_calls]
        assert call_names.index("read_blocked") < call_names.index("get_status")

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True)
    @patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True)
    @patch(
        "mcp_coder.workflows.implement.core.get_full_status",
        return_value={"staged": [], "modified": [], "untracked": []},
    )
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
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    @patch("mcp_coder.workflows.implement.core.read_and_clear_blocked")
    def test_format_code_false_skips_formatter(
        self,
        _mock_read_blocked: MagicMock,
        _mock_check_git: MagicMock,
        _mock_check_branch: MagicMock,
        _mock_check_prereq: MagicMock,
        _mock_prepare_tracker: MagicMock,
        _mock_log_progress: MagicMock,
        mock_process_task: MagicMock,
        _mock_get_branch: MagicMock,
        _mock_prepare_env: MagicMock,
        mock_check_mypy: MagicMock,
        _mock_get_status: MagicMock,
        _mock_run_finalisation: MagicMock,
        _mock_check_ci: MagicMock,
        mock_run_format_code: MagicMock,
        tmp_path: Path,
    ) -> None:
        """``format_code = false`` → the post-mypy formatting never calls the formatter."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder]\nformat_code = false\n\n"
            "[tool.mcp-coder.implement]\ncheck_type_hints = true\n",
            encoding="utf-8",
        )
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]

        result = run_implement_workflow(tmp_path, "claude")

        assert result == 0
        mock_check_mypy.assert_called_once()
        mock_run_format_code.assert_not_called()
