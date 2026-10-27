from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.task_processing import (
    check_and_fix_mypy,
    process_single_task,
)
from tests.workflows.implement.test_task_processing import _make_llm_response


class TestBranchNameSource:
    """The LLM-log branch name is read from project_dir.

    project_dir is also the subprocess working directory, so each test asserts
    prompt_llm keeps receiving it.
    """

    _PROJECT_DIR = Path("/test/project")

    @patch("mcp_coder.workflows.implement.task_processing.get_branch_name_for_logging")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_implementation_path_reads_branch_from_project_dir(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_get_status: MagicMock,
        mock_store_session: MagicMock,
        mock_branch_name: MagicMock,
    ) -> None:
        """The branch lookup and the subprocess cwd both come from project_dir."""
        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}
        mock_branch_name.return_value = "feature-branch"

        process_single_task(self._PROJECT_DIR, "claude")

        mock_branch_name.assert_called_once_with(str(self._PROJECT_DIR))
        assert mock_prompt_llm.call_args.kwargs["project_dir"] == str(self._PROJECT_DIR)
        assert mock_prompt_llm.call_args.kwargs["branch_name"] == "feature-branch"
        mock_store_session.assert_called_once()

    @patch("mcp_coder.workflows.implement.task_processing.get_branch_name_for_logging")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_mypy_fix_path_reads_branch_from_project_dir(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_branch_name: MagicMock,
    ) -> None:
        """The mypy-fix call site is separate code and needs its own coverage."""
        mock_mypy_check.side_effect = ["mypy error output", None]
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.return_value = _make_llm_response("Fixed the errors")
        mock_branch_name.return_value = "feature-branch"

        result = check_and_fix_mypy(self._PROJECT_DIR, 1, "claude")

        assert result is True
        mock_branch_name.assert_called_once_with(str(self._PROJECT_DIR))
        assert mock_prompt_llm.call_args.kwargs["project_dir"] == str(self._PROJECT_DIR)
        assert mock_prompt_llm.call_args.kwargs["branch_name"] == "feature-branch"
        mock_store_session.assert_called_once()
