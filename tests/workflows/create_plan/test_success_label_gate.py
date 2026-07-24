"""Tests for the config-gated success label transition in create_plan."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.create_plan import run_create_plan_workflow

# Common patch prefixes
_CORE = "mcp_coder.workflows.create_plan.core"
_PREREQ = "mcp_coder.workflows.create_plan.prerequisites"


class TestSuccessLabelGate:
    """Tests for the config-gated success label transition."""

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

    def _run_success_path(
        self,
        mock_issue_data: IssueData,
        tmp_path: Path,
        *,
        flag: bool,
    ) -> tuple[int, MagicMock]:
        """Drive the workflow to the label transition and return (result, mock)."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(
                f"{_CORE}.check_prerequisites",
                return_value=(True, mock_issue_data),
            ),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(f"{_CORE}.run_planning_prompts", return_value=(True, None)),
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(
                f"{_CORE}.commit_all_changes",
                return_value={"success": True, "commit_hash": "abc123"},
            ),
            patch(f"{_CORE}.git_push", return_value={"success": True}),
            patch(f"{_PREREQ}.IssueManager"),
            patch(f"{_PREREQ}.get_repo_flag", return_value=flag),
            patch(f"{_PREREQ}.update_workflow_label", return_value=True) as mock_update,
        ):
            result = run_create_plan_workflow(
                123, tmp_path, "claude", update_issue_labels=True
            )
        return result, mock_update

    def test_flag_off_uses_plan_review(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Flag off → success label transitions to plan_review."""
        result, mock_update = self._run_success_path(
            mock_issue_data, tmp_path, flag=False
        )

        assert result == 0
        mock_update.assert_called_once()
        assert mock_update.call_args.kwargs["from_label_id"] == "planning"
        assert mock_update.call_args.kwargs["to_label_id"] == "plan_review"
        assert mock_update.call_args.kwargs["validated_issue_number"] == 123

    def test_flag_on_uses_plan_review_bot(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Flag on → success label transitions to plan_review_bot."""
        result, mock_update = self._run_success_path(
            mock_issue_data, tmp_path, flag=True
        )

        assert result == 0
        mock_update.assert_called_once()
        assert mock_update.call_args.kwargs["from_label_id"] == "planning"
        assert mock_update.call_args.kwargs["to_label_id"] == "plan_review_bot"
        assert mock_update.call_args.kwargs["validated_issue_number"] == 123
