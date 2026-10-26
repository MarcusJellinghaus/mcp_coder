"""Tests for create_pr workflow orchestration."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.create_pr.core import run_create_pr_workflow


@pytest.fixture(autouse=True)
def mock_post_creation() -> Iterator[MagicMock]:
    """Phase B never polls GitHub in these tests."""
    with patch(
        "mcp_coder.workflows.create_pr.core.run_post_creation",
        return_value="pr_created",
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_find_open_pr() -> Iterator[MagicMock]:
    """No open PR for the branch: the normal phase A runs."""
    with patch(
        "mcp_coder.workflows.create_pr.core._find_open_pr", return_value=None
    ) as mock:
        yield mock


class TestRunCreatePrWorkflow:
    """Test suite for run_create_pr_workflow orchestration."""

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_complete_success(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
    ) -> None:
        """Test successful workflow with all steps completing."""
        # Setup mocks
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = False  # Has changes to commit
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        # Execute
        result = run_create_pr_workflow(Path("/test"), "claude")

        # Verify
        assert result == 0
        mock_prereqs.assert_called_once_with(Path("/test"))
        mock_generate.assert_called_once_with(Path("/test"), "claude", None, None)
        mock_create_pr.assert_called_once_with(Path("/test"), "Test Title", "Test Body")
        mock_cleanup.assert_called_once_with(Path("/test"))
        mock_commit.assert_called_once()
        # git_push should be called once (cleanup happens before push)
        assert mock_push.call_count == 1

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_prerequisites_fail(
        self,
        _mock_rebase: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test workflow exits when prerequisites fail."""
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_prereqs.assert_called_once_with(Path("/test"))
        mock_handle_failure.assert_called_once()
        assert mock_handle_failure.call_args.kwargs["stage"] == "prerequisites"

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_pr_creation_fails(
        self,
        _mock_rebase: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test workflow exits when PR creation fails."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (None, "GitHub API error: 422 Validation Failed")

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_create_pr.assert_called_once_with(Path("/test"), "Title", "Body")
        mock_handle_failure.assert_called_once()
        assert mock_handle_failure.call_args.kwargs["stage"] == "pr_creation"
        assert (
            "422 Validation Failed" in mock_handle_failure.call_args.kwargs["message"]
        )

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_generate_summary_exception(
        self,
        _mock_rebase: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
    ) -> None:
        """Test workflow handles generate_pr_summary exceptions."""
        mock_prereqs.return_value = True
        mock_generate.side_effect = ValueError("LLM failed")

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_generate.assert_called_once_with(Path("/test"), "claude", None, None)
        mock_handle_failure.assert_called_once()
        assert mock_handle_failure.call_args.kwargs["stage"] == "summary_generation"

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_session_params_passed_to_generate_summary(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test project_dir and session params are passed to generate_pr_summary."""
        # Setup mocks
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True  # Clean directory, no commit needed
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(tmp_path, "claude", None)

        # Verify
        assert result == 0
        mock_generate.assert_called_once_with(tmp_path, "claude", None, None)

    @patch(
        "mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage",
        return_value=123,
    )
    @patch("mcp_coder.workflows.create_pr.core._add_pr_assignee_best_effort")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_appends_closing_reference_without_label_updates(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        _mock_add_assignee: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Linked issue is closed by the PR body even without label updates."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 0
        mock_validate.assert_called_once_with(Path("/test"))
        mock_create_pr.assert_called_once_with(
            Path("/test"), "Title", "Body\n\nCloses #123"
        )

    @patch("mcp_coder.workflows.create_pr.core._add_pr_assignee_best_effort")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_leaves_body_unchanged_when_not_linked(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        _mock_add_assignee: MagicMock,
    ) -> None:
        """PR body is passed through unchanged when the branch is not linked."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 0
        mock_create_pr.assert_called_once_with(Path("/test"), "Title", "Body")


class TestRunCreatePrWorkflowAfterCreation:
    """Phase A steps that run after the PR is created, and step ordering."""

    @patch("mcp_coder.workflows.create_pr.core._add_pr_assignee_best_effort")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_assigns_pr_on_success(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_add_assignee: MagicMock,
    ) -> None:
        """Assignee-add runs after a successful PR creation with the PR number."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 0
        mock_add_assignee.assert_called_once_with(Path("/test"), 42)

    @patch("mcp_coder.workflows.create_pr.core._add_pr_assignee_best_effort")
    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_skips_assignee_add_on_pr_failure(
        self,
        _mock_rebase: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_handle_failure: MagicMock,
        mock_add_assignee: MagicMock,
    ) -> None:
        """Assignee-add is skipped when PR creation fails (not on a failed path)."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (None, "GitHub API error")

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 1
        mock_add_assignee.assert_not_called()

    @patch("mcp_coder.workflows.create_pr.core._add_pr_assignee_best_effort")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_rebases_before_summary(
        self,
        mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        _mock_add_assignee: MagicMock,
    ) -> None:
        """Rebase-if-needed runs once, after prerequisites, before the summary."""
        manager = MagicMock()
        manager.attach_mock(mock_prereqs, "prereqs")
        manager.attach_mock(mock_rebase, "rebase")
        manager.attach_mock(mock_generate, "generate")
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 0
        mock_rebase.assert_called_once_with(Path("/test"))
        names = [c[0] for c in manager.mock_calls]
        assert names == ["prereqs", "rebase", "generate"]

    @patch("mcp_coder.workflows.create_pr.core._handle_create_pr_failure")
    @patch("mcp_coder.workflows.create_pr.core._add_pr_assignee_best_effort")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_continues_when_rebase_push_fails(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        _mock_add_assignee: MagicMock,
        mock_failure: MagicMock,
    ) -> None:
        """Pre-PR rebase push fails → HEAD restored, PR still created, no 09f."""
        pre = "mcp_coder.workflows.create_pr.pre_creation"
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        with (
            patch(f"{pre}.get_current_branch_name", return_value="feature-branch"),
            patch(f"{pre}.detect_base_branch", return_value="main"),
            patch(f"{pre}.needs_rebase", return_value=(True, "behind")),
            patch(f"{pre}.get_latest_commit_sha", return_value="before"),
            patch(
                f"{pre}._attempt_rebase_and_push",
                return_value=RebaseOutcome(reason="push_failed", base_branch="main"),
            ),
            patch(f"{pre}._reset_hard", return_value=True) as mock_reset,
        ):
            result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 0
        mock_reset.assert_called_once_with(Path("/test"), "before")
        mock_push.assert_called_once_with(Path("/test"))
        mock_create_pr.assert_called_once()
        mock_failure.assert_not_called()
