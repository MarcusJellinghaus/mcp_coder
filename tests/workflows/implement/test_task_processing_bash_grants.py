"""Tests for the Bash grants of the implement task session."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.implement.task_processing import process_single_task
from tests.workflows.implement.test_task_processing import _make_llm_response


class TestProcessSingleTaskBashGrants:
    """The implement task call passes the toolkit's Bash grants."""

    @patch(
        "mcp_coder.workflows.implement.task_processing._count_incomplete_tasks",
        return_value=0,
    )
    @patch(
        "mcp_coder.workflows.implement.task_processing.get_binding",
        return_value=(),
    )
    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    @patch(
        "mcp_coder.workflows.implement.task_processing.llm_permissions",
        return_value=["Bash(npm test)", "mcp__x__y"],
    )
    def test_passes_bash_grants(
        self,
        mock_perms: MagicMock,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        _mock_run_formatters: MagicMock,
        _mock_commit: MagicMock,
        _mock_push: MagicMock,
        _mock_get_binding: MagicMock,
        _mock_count: MagicMock,
    ) -> None:
        """Only the Bash entries reach prompt_llm."""
        project = Path("/test/project")
        mock_get_incomplete.return_value = ["Step 1: Create test file"]
        mock_get_prompt.return_value = "Implementation template"
        mock_prompt_llm.return_value = _make_llm_response("LLM response")
        mock_get_status.return_value = {
            "staged": ["file1.py"],
            "modified": [],
            "untracked": [],
        }

        process_single_task(project, "claude")

        mock_perms.assert_called_once_with(project, "claude")
        assert mock_prompt_llm.call_args.kwargs["bash_grants"] == ["Bash(npm test)"]


class TestProcessSingleTaskPromptSlots:
    """The template's slots are filled before the task line is appended."""

    def test_template_filled_before_task_line(self) -> None:
        """The slot value is inserted; a slot name inside the task stays literal."""
        base = "mcp_coder.workflows.implement.task_processing"
        project = Path("/test/project")
        task = "Step 1: Document the [check_instructions] slot"
        with (
            patch(f"{base}.llm_permissions", return_value=["Bash(npm test)"]),
            patch(f"{base}.get_incomplete_tasks", return_value=[task]),
            patch(
                f"{base}.get_prompt",
                return_value="Template\n\n[check_instructions]\n\nEnd",
            ),
            patch(
                f"{base}.resolve_prompt_slots",
                return_value={"check_instructions": "Run npm test."},
            ) as mock_slots,
            patch(f"{base}.prompt_llm") as mock_prompt_llm,
            patch(f"{base}.store_session"),
            patch(
                f"{base}.get_full_status",
                return_value={"staged": [], "modified": [], "untracked": []},
            ),
        ):
            mock_prompt_llm.return_value = _make_llm_response("LLM response")
            process_single_task(project, "claude")

        prompt: str = mock_prompt_llm.call_args.args[0]
        assert prompt.startswith("Template\n\nRun npm test.\n\nEnd")
        assert f"Current task from TASK_TRACKER.md: {task}" in prompt
        assert mock_slots.call_args.args[3] == ["Bash(npm test)"]
        assert mock_prompt_llm.call_args.kwargs["bash_grants"] == ["Bash(npm test)"]
