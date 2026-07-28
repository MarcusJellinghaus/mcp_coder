"""Tests for create_plan failure-comment formatting and failure routing."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflow_utils.failure_handling import WorkflowFailure
from mcp_coder.workflows.create_plan import (
    _format_failure_comment,
    _handle_workflow_failure,
    run_create_plan_workflow,
)

# Common patch prefix
_CORE = "mcp_coder.workflows.create_plan.core"


class TestFormatFailureComment:
    """Tests for _format_failure_comment."""

    def test_general_failure_comment(self) -> None:
        """Test general failure comment (no Category / prompt_stage lines)."""
        failure = WorkflowFailure(
            category="planning_failed",
            stage="Output validation",
            message="Required output files not found",
            elapsed_time=2.0,
        )
        comment = _format_failure_comment(failure, "")
        assert "## Planning Failed" in comment
        assert "**Stage:** Output validation" in comment
        assert "**Error:** Required output files not found" in comment
        assert "Category" not in comment
        assert "Prompt stage" not in comment

    def test_elapsed_time_formatting(self) -> None:
        """Test elapsed time is formatted correctly."""
        failure = WorkflowFailure(
            category="planning_failed",
            stage="test",
            message="test",
            elapsed_time=605.0,
        )
        comment = _format_failure_comment(failure, "")
        assert "**Elapsed:** 10m 5s" in comment

    def test_no_elapsed_time_when_none(self) -> None:
        """Test no elapsed line when elapsed_time is None."""
        failure = WorkflowFailure(
            category="planning_failed",
            stage="test",
            message="test",
        )
        comment = _format_failure_comment(failure, "")
        assert "Elapsed" not in comment

    def test_uncommitted_changes_section(self) -> None:
        """Test uncommitted changes section with diff stat."""
        failure = WorkflowFailure(
            category="planning_failed",
            stage="test",
            message="test",
        )
        comment = _format_failure_comment(failure, " file1.py | 5 ++--\n")
        assert "### Uncommitted Changes" in comment
        assert "file1.py" in comment

    def test_no_uncommitted_changes_section_when_empty(self) -> None:
        """Test no uncommitted changes section when diff_stat is empty."""
        failure = WorkflowFailure(
            category="planning_failed",
            stage="test",
            message="test",
        )
        comment = _format_failure_comment(failure, "")
        assert "Uncommitted Changes" not in comment


class TestHandleWorkflowFailure:
    """Tests for _handle_workflow_failure."""

    def test_calls_shared_handler_with_correct_args(self, tmp_path: Path) -> None:
        """Test shared handler is called with correct arguments."""
        failure = WorkflowFailure(
            category="planning_llm_timeout",
            stage="Prompt 2 (timeout)",
            message="Timed out",
            elapsed_time=100.0,
        )

        with (
            patch(f"{_CORE}.get_diff_stat", return_value=""),
            patch(f"{_CORE}.handle_workflow_failure") as mock_shared,
        ):
            _handle_workflow_failure(failure, tmp_path, True, True, issue_number=42)

        mock_shared.assert_called_once()
        call_kwargs = mock_shared.call_args[1]
        assert call_kwargs["failure"].category == "planning_llm_timeout"
        assert call_kwargs["failure"].stage == "Prompt 2 (timeout)"
        assert call_kwargs["from_label_id"] == "planning"
        assert call_kwargs["update_issue_labels"] is True
        assert call_kwargs["post_issue_comments"] is True
        # issue_number is now forwarded so label/comment can target the issue
        # even when the caller is not on the issue branch.
        assert call_kwargs["issue_number"] == 42

    def test_respects_flags(self, tmp_path: Path) -> None:
        """Test flags are passed through correctly."""
        failure = WorkflowFailure(
            category="planning_failed",
            stage="test",
            message="test",
        )

        with (
            patch(f"{_CORE}.get_diff_stat", return_value=""),
            patch(f"{_CORE}.handle_workflow_failure") as mock_shared,
        ):
            _handle_workflow_failure(failure, tmp_path, False, False, issue_number=7)

        call_kwargs = mock_shared.call_args[1]
        assert call_kwargs["update_issue_labels"] is False
        assert call_kwargs["post_issue_comments"] is False
        assert call_kwargs["issue_number"] == 7


class TestFailureHandling:
    """Integration tests for failure handling in run_create_plan_workflow."""

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

    def test_prerequisites_dirty_git_failure(self, tmp_path: Path) -> None:
        """Test failure handling when git working directory is dirty."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=False),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        mock_handler.assert_called_once()
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_prereq_failed"
        assert failure.stage == "Prerequisites (git working directory not clean)"
        assert mock_handler.call_args.kwargs["issue_number"] == 123

    def test_prerequisites_issue_not_found_failure(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test failure handling when issue is not found."""
        (tmp_path / ".git").mkdir()
        empty_issue = IssueData(
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
            patch(f"{_CORE}.check_prerequisites", return_value=(False, empty_issue)),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_prereq_failed"
        assert failure.stage == "Prerequisites (issue not found)"
        assert mock_handler.call_args.kwargs["issue_number"] == 123

    def test_branch_failure(self, mock_issue_data: IssueData, tmp_path: Path) -> None:
        """Test failure handling when branch creation fails."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value=None),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_prereq_failed"
        assert failure.stage == "Branch management (branch creation failed)"
        assert mock_handler.call_args.kwargs["issue_number"] == 123

    def test_pr_info_exists_failure(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test failure handling when pr_info/ already exists."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=False),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_prereq_failed"
        assert failure.stage == "Workspace setup (pr_info/ already exists)"
        assert mock_handler.call_args.kwargs["issue_number"] == 123

    def test_pr_info_create_failure(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test failure handling when pr_info directory creation fails."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=False),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_prereq_failed"
        assert failure.stage == "Workspace setup (directory creation failed)"
        assert mock_handler.call_args.kwargs["issue_number"] == 123

    def test_planning_timeout_failure(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test failure handling when planning prompts timeout."""
        (tmp_path / ".git").mkdir()
        prompt_failure = WorkflowFailure(
            category="planning_llm_timeout",
            stage="Prompt 2 (timeout)",
            message="LLM request timed out after 600s",
        )

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(
                f"{_CORE}.run_planning_prompts", return_value=(False, prompt_failure)
            ),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_llm_timeout"
        # elapsed_time should be replaced by orchestrator (not None)
        assert failure.elapsed_time is not None

    def test_validate_output_failure(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test failure handling when output validation fails."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(f"{_CORE}.run_planning_prompts", return_value=(True, None)),
            patch(f"{_CORE}.validate_output_files", return_value=False),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_failed"
        assert failure.stage == "Output validation"

    def test_commit_failure(self, mock_issue_data: IssueData, tmp_path: Path) -> None:
        """Test failure handling when commit fails."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(f"{_CORE}.run_planning_prompts", return_value=(True, None)),
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(
                f"{_CORE}.commit_all_changes",
                return_value={"success": False, "error": "Commit failed"},
            ),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_failed"
        assert failure.stage == "Commit & push"

    def test_push_failure(self, mock_issue_data: IssueData, tmp_path: Path) -> None:
        """Test failure handling when push fails."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=True),
            patch(f"{_CORE}.check_prerequisites", return_value=(True, mock_issue_data)),
            patch(f"{_CORE}.manage_branch", return_value="feature-branch"),
            patch(f"{_CORE}.check_pr_info_not_exists", return_value=True),
            patch(f"{_CORE}.create_pr_info_structure", return_value=True),
            patch(f"{_CORE}.run_planning_prompts", return_value=(True, None)),
            patch(f"{_CORE}.validate_output_files", return_value=True),
            patch(
                f"{_CORE}.commit_all_changes",
                return_value={"success": True, "commit_hash": "abc123"},
            ),
            patch(
                f"{_CORE}.git_push",
                return_value={"success": False, "error": "Push failed"},
            ),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        failure = mock_handler.call_args[0][0]
        assert failure.category == "planning_failed"
        assert failure.stage == "Commit & push"

    def test_handler_called_when_flags_false(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test _handle_workflow_failure still called even when flags are False."""
        (tmp_path / ".git").mkdir()

        with (
            patch(f"{_CORE}.is_working_directory_clean", return_value=False),
            patch(f"{_CORE}._handle_workflow_failure") as mock_handler,
        ):
            result = run_create_plan_workflow(
                123,
                tmp_path,
                "claude",
                update_issue_labels=False,
                post_issue_comments=False,
            )

        assert result == 1
        mock_handler.assert_called_once()
        # Verify flags passed through
        assert mock_handler.call_args[0][2] is False  # update_issue_labels
        assert mock_handler.call_args[0][3] is False  # post_issue_comments
