"""Tests for create_plan workflow main orchestration."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflow_utils.failure_handling import WorkflowFailure
from mcp_coder.workflows.create_plan import run_create_plan_workflow

# Common patch prefix
_CORE = "mcp_coder.workflows.create_plan.core"


class TestMain:
    """Test main workflow orchestration function."""

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

    def _run_workflow_with_patches(  # noqa: PLR0913
        self,
        tmp_path: Path,
        mock_issue_data: IssueData,
        *,
        is_clean: bool = True,
        check_prereqs: tuple[bool, IssueData] | None = None,
        manage_branch_rv: str | None = "feature-branch",
        pr_info_not_exists: bool = True,
        create_pr_info: bool = True,
        planning_prompts_rv: tuple[bool, WorkflowFailure | None] = (True, None),
        validate_output: bool = True,
        commit_rv: dict[str, object] | None = None,
        push_rv: dict[str, object] | None = None,
        issue_number: int = 123,
        provider: str = "claude",
        mcp_config: str | None = None,
        update_issue_labels: bool = False,
        post_issue_comments: bool = False,
    ) -> int:
        """Helper to run workflow with configurable patches."""
        if check_prereqs is None:
            check_prereqs = (True, mock_issue_data)
        if commit_rv is None:
            commit_rv = {"success": True, "commit_hash": "abc123"}
        if push_rv is None:
            push_rv = {"success": True}

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=is_clean),
            patch(f"{_CORE}.check_prerequisites", return_value=check_prereqs),
            patch(f"{_CORE}.manage_branch", return_value=manage_branch_rv),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=pr_info_not_exists),
            patch(f"{_CORE}.create_pr_info_structure", return_value=create_pr_info),
            patch(f"{_CORE}.run_planning_prompts", return_value=planning_prompts_rv),
            patch(f"{_CORE}.validate_output_files", return_value=validate_output),
            patch(f"{_CORE}.commit_all_changes", return_value=commit_rv),
            patch(f"{_CORE}.git_push", return_value=push_rv),
            patch(f"{_CORE}._handle_workflow_failure"),
        ):
            return run_create_plan_workflow(
                issue_number,
                tmp_path,
                provider,
                mcp_config,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )

    def test_main_success_flow(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function with successful workflow execution."""
        (tmp_path / ".git").mkdir()
        result = self._run_workflow_with_patches(tmp_path, mock_issue_data)
        assert result == 0

    def test_main_session_params_passed_to_prompts(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test project_dir and session params are passed to run_planning_prompts."""
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
            patch(
                f"{_CORE}.run_planning_prompts",
                return_value=(True, None),
            ) as mock_prompts,
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(
                f"{_CORE}.commit_all_changes",
                return_value={"success": True, "commit_hash": "abc123"},
            ),
            patch(f"{_CORE}.git_push", return_value={"success": True}),
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude", None)

        assert result == 0
        mock_prompts.assert_called_once_with(
            tmp_path, mock_issue_data, "claude", None, None
        )

    def test_main_prerequisites_fail(self, tmp_path: Path) -> None:
        """Test main function when prerequisites validation fails."""
        (tmp_path / ".git").mkdir()

        empty_issue_data = IssueData(
            number=0,
            title="",
            body="",
            state="",
            labels=[],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="",
            locked=False,
        )

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(
                f"{_CORE}.check_prerequisites",
                return_value=(False, empty_issue_data),
            ),
            patch(f"{_CORE}._handle_workflow_failure"),
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1

    def test_main_branch_management_fail(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when branch management fails."""
        (tmp_path / ".git").mkdir()
        result = self._run_workflow_with_patches(
            tmp_path, mock_issue_data, manage_branch_rv=None
        )
        assert result == 1

    def test_main_pr_info_exists(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when pr_info/ directory already exists."""
        (tmp_path / ".git").mkdir()
        result = self._run_workflow_with_patches(
            tmp_path, mock_issue_data, pr_info_not_exists=False
        )
        assert result == 1

    def test_main_create_pr_info_structure_fails(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when create_pr_info_structure fails."""
        (tmp_path / ".git").mkdir()
        result = self._run_workflow_with_patches(
            tmp_path, mock_issue_data, create_pr_info=False
        )
        assert result == 1

    def test_main_planning_prompts_fail(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when planning prompts execution fails."""
        (tmp_path / ".git").mkdir()
        failure = WorkflowFailure(
            category="planning_failed",
            stage="Prompt 1 (general)",
            message="LLM error",
        )
        result = self._run_workflow_with_patches(
            tmp_path, mock_issue_data, planning_prompts_rv=(False, failure)
        )
        assert result == 1

    def test_main_validation_fail(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when output files validation fails."""
        (tmp_path / ".git").mkdir()
        result = self._run_workflow_with_patches(
            tmp_path, mock_issue_data, validate_output=False
        )
        assert result == 1

    def test_main_commit_message_format(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function uses correct commit message format."""
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
            patch(
                f"{_CORE}.run_planning_prompts",
                return_value=(True, None),
            ),
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(f"{_CORE}.commit_all_changes") as mock_commit,
            patch(f"{_CORE}.git_push", return_value={"success": True}),
        ):
            mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
            result = run_create_plan_workflow(123, tmp_path, "claude")

        mock_commit.assert_called_once()
        commit_message = mock_commit.call_args[0][0]
        assert commit_message == "Initial plan generated for issue #123"
        assert result == 0

    def test_main_commit_fails_returns_error(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function returns error when commit fails."""
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
            patch(
                f"{_CORE}.run_planning_prompts",
                return_value=(True, None),
            ),
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(
                f"{_CORE}.commit_all_changes",
                return_value={"success": False, "error": "Commit failed"},
            ),
            patch(f"{_CORE}.git_push") as mock_push,
            patch(f"{_CORE}._handle_workflow_failure"),
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        # Push should NOT be called (workflow exits before push)
        mock_push.assert_not_called()

    def test_main_push_fails_returns_error(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function returns error when push fails."""
        (tmp_path / ".git").mkdir()
        result = self._run_workflow_with_patches(
            tmp_path,
            mock_issue_data,
            push_rv={"success": False, "error": "Push failed"},
        )
        assert result == 1

    def test_main_with_custom_project_dir(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function with custom project directory."""
        custom_dir = tmp_path / "custom_project"
        custom_dir.mkdir()
        (custom_dir / ".git").mkdir()

        result = self._run_workflow_with_patches(
            custom_dir,
            mock_issue_data,
            issue_number=456,
            provider="claude_code",
            mcp_config="api",
        )
        assert result == 0

    def test_main_logging_includes_issue_details(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function logs include issue number and title."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(
                f"{_CORE}.check_prerequisites",
                return_value=(True, mock_issue_data),
            ) as mock_check,
            patch(
                f"{_CORE}.manage_branch", return_value="feature-branch"
            ) as mock_manage,
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(
                f"{_CORE}.run_planning_prompts",
                return_value=(True, None),
            ) as mock_prompts,
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(
                f"{_CORE}.commit_all_changes",
                return_value={"success": True, "commit_hash": "abc123"},
            ),
            patch(f"{_CORE}.git_push", return_value={"success": True}),
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        mock_check.assert_called_once_with(tmp_path, 123)
        mock_manage.assert_called_once_with(
            tmp_path, 123, "Test Issue", base_branch=None
        )
        mock_prompts.assert_called_once_with(
            tmp_path, mock_issue_data, "claude", None, None, None
        )
        assert result == 0
