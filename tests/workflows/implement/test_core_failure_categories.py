"""Tests for implement workflow failure categorization (exception -> category).

Split out of test_core.py, which sits close to the CI file-size gate
(`mcp-coder check file-size --max-lines 750`).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_processing import TaskOutcome


class TestRunImplementWorkflowFailureCategories:
    """Test that final-mypy and CI-analysis exceptions get the right category."""

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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

        mock_get_config.return_value = ImplementConfig(check_type_hints=True)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]
        mock_check_mypy.side_effect = LLMTimeoutError("timed out")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "llm_timeout"
        assert failure_arg.stage == "Final mypy check"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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

        mock_get_config.return_value = ImplementConfig(check_type_hints=True)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]
        mock_check_mypy.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "mcp_unavailable"
        assert failure_arg.stage == "Final mypy check"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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

        mock_get_config.return_value = ImplementConfig(check_type_hints=True)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]
        mock_check_ci.side_effect = LLMTimeoutError("timed out")

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "llm_timeout"
        assert failure_arg.stage == "CI pipeline analysis"

    @patch("mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure")
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

        mock_get_config.return_value = ImplementConfig(check_type_hints=True)
        mock_check_git.return_value = True
        mock_check_branch.return_value = True
        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.side_effect = [
            TaskOutcome(True, "completed"),
            TaskOutcome(False, "no_tasks"),
        ]
        mock_check_ci.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        result = run_implement_workflow(Path("/test/project"), "claude")

        assert result == 1
        mock_handle_failure.assert_called_once()
        failure_arg = mock_handle_failure.call_args[1]["failure"]
        assert failure_arg.category == "mcp_unavailable"
        assert failure_arg.stage == "CI pipeline analysis"
