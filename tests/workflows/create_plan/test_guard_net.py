"""Tests for the run_guarded safety net around the create_plan orchestrator."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.create_plan import run_create_plan_workflow

# Common patch prefix
_CORE = "mcp_coder.workflows.create_plan.core"

# Shared handler run_guarded invokes on a netted escape.
_SHARED_HANDLER = "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"


class TestGuardNet:
    """Tests for the run_guarded safety net around the orchestrator body."""

    @pytest.fixture
    def mock_issue_data(self) -> IssueData:
        """Create mock issue data for testing."""
        return IssueData(
            number=123,
            title="Test Issue",
            body="Test issue body",
            state="open",
            labels=["enhancement"],
            assignees=["testuser"],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

    def test_system_exit_netted_to_planning_failed(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """A body escape via sys.exit(1) is netted to the general label.

        Mirrors ``_load_prompt_or_exit -> sys.exit(1)``: the guard nets the
        escape into ``planning_failed`` (posting a comment) and re-raises the
        ``SystemExit``.
        """
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(f"{_CORE}.run_planning_prompts", side_effect=SystemExit(1)),
            patch(_SHARED_HANDLER) as mock_shared,
        ):
            with pytest.raises(SystemExit):
                run_create_plan_workflow(
                    123,
                    tmp_path,
                    "claude",
                    update_issue_labels=True,
                    post_issue_comments=True,
                )

        mock_shared.assert_called_once()
        netted_failure = mock_shared.call_args[0][0]
        assert netted_failure.category == "planning_failed"

    def test_unexpected_exception_netted_to_planning_failed(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """An unexpected exception escaping the body is netted and returns 1."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(
                f"{_CORE}.run_planning_prompts",
                side_effect=RuntimeError("unexpected boom"),
            ),
            patch(_SHARED_HANDLER) as mock_shared,
        ):
            result = run_create_plan_workflow(
                123,
                tmp_path,
                "claude",
                update_issue_labels=True,
                post_issue_comments=True,
            )

        assert result == 1
        mock_shared.assert_called_once()
        netted_failure = mock_shared.call_args[0][0]
        assert netted_failure.category == "planning_failed"
