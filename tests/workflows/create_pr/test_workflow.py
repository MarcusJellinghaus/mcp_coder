"""Tests for create_pr workflow orchestration."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import (
    run_create_pr_workflow,
    validate_branch_issue_linkage,
)


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
    def test_workflow_complete_success(
        self,
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
    def test_workflow_prerequisites_fail(
        self, mock_prereqs: MagicMock, mock_handle_failure: MagicMock
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
    def test_workflow_pr_creation_fails(
        self,
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
    def test_workflow_generate_summary_exception(
        self,
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
    def test_workflow_execution_dir_passed_to_generate_summary(
        self,
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
        """Test execution_dir parameter is passed to generate_pr_summary."""
        # Create execution_dir
        exec_dir = tmp_path / "execution"
        exec_dir.mkdir()

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

        # Execute with execution_dir
        result = run_create_pr_workflow(tmp_path, "claude", None, exec_dir)

        # Verify
        assert result == 0
        # Verify execution_dir was passed to generate_pr_summary
        mock_generate.assert_called_once_with(tmp_path, "claude", None, exec_dir)

    @patch("mcp_coder.workflows.create_pr.core.update_workflow_label")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    @patch("mcp_coder.mcp_workspace_github.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_caches_issue_number_before_pr_creation(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_update_label: MagicMock,
    ) -> None:
        """Tests that workflow caches issue number before PR creation."""
        # Setup: Mock validate_branch_issue_linkage to return 123
        mock_validate.return_value = 123
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

        # Setup IssueManager mock
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_update_label.return_value = True

        # Call: run_create_pr_workflow(..., update_issue_labels=True)
        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        # Assert: update_workflow_label called with validated_issue_number=123
        assert result == 0
        mock_validate.assert_called_once_with(Path("/test"))
        mock_update_label.assert_called_once_with(
            mock_issue_manager,
            from_label_id="pr_creating",
            to_label_id="pr_created",
            validated_issue_number=123,
        )

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    @patch("mcp_coder.mcp_workspace_github.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_skips_label_update_when_not_linked(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
    ) -> None:
        """Tests that workflow skips label update when branch not linked."""
        # Setup: Mock validate_branch_issue_linkage to return None
        mock_validate.return_value = None
        # Setup: Mock PullRequestManager fallback to return no closing issues
        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = []
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

        # Setup IssueManager mock
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Call: run_create_pr_workflow(..., update_issue_labels=True)
        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        # Assert: update_workflow_label NOT called
        assert result == 0
        mock_validate.assert_called_once_with(Path("/test"))
        mock_issue_manager.update_workflow_label.assert_not_called()

    @patch("mcp_coder.workflows.create_pr.core.update_workflow_label")
    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.mcp_workspace_github.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_fallback_finds_issue_via_closing_references(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        mock_update_label: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests fallback queries closingIssuesReferences and finds issue."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = [92]

        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_update_label.return_value = True

        with caplog.at_level(logging.DEBUG):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 0
        mock_pr_mgr.get_closing_issue_numbers.assert_called_once_with(42)
        mock_update_label.assert_called_once_with(
            mock_issue_manager,
            from_label_id="pr_creating",
            to_label_id="pr_created",
            validated_issue_number=92,
        )
        assert "completed successfully!" in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.update_workflow_label")
    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.mcp_workspace_github.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_fallback_multiple_closing_issues_uses_first(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        mock_update_label: MagicMock,
    ) -> None:
        """Tests fallback with multiple closing issues uses first."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = [92, 55]

        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_update_label.return_value = True

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_update_label.assert_called_once_with(
            mock_issue_manager,
            from_label_id="pr_creating",
            to_label_id="pr_created",
            validated_issue_number=92,
        )

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_fallback_no_closing_issues_skips_labels(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests fallback with no closing issues skips label update."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = []

        with caplog.at_level(logging.DEBUG):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 0
        assert "completed with warnings" in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_completed_with_warnings_when_no_issue_found(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests completion message is 'with warnings' when no issue found."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = []

        with caplog.at_level(logging.DEBUG):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 0
        assert "completed with warnings" in caplog.text
        assert "completed successfully!" not in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.mcp_workspace_github.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    def test_workflow_skips_fallback_when_issue_already_found(
        self,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
    ) -> None:
        """Tests that fallback is skipped when issue already found from branch."""
        mock_validate.return_value = 123
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_issue_manager.update_workflow_label.return_value = True
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "123-feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_pr_manager_class.return_value.get_closing_issue_numbers.assert_not_called()


class TestValidateBranchIssueLinkage:
    """Test suite for validate_branch_issue_linkage helper function."""

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.IssueBranchManager")
    def test_validate_branch_issue_linkage_success(
        self, mock_manager_class: MagicMock, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests successful validation when branch is linked to issue."""
        # Setup: Mock branch name "123-feature", linked branches ["123-feature"]
        mock_get_branch.return_value = "123-feature"
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_linked_branches.return_value = ["123-feature"]

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns 123
        assert result == 123
        mock_get_branch.assert_called_once_with(tmp_path)
        mock_manager_class.assert_called_once_with(project_dir=tmp_path)
        mock_manager.get_linked_branches.assert_called_once_with(123)

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.IssueBranchManager")
    def test_validate_branch_issue_linkage_not_linked(
        self, mock_manager_class: MagicMock, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation fails when branch is not linked."""
        # Setup: Mock branch name "123-feature", linked branches []
        mock_get_branch.return_value = "123-feature"
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_linked_branches.return_value = []

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)
        mock_manager_class.assert_called_once_with(project_dir=tmp_path)
        mock_manager.get_linked_branches.assert_called_once_with(123)

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    def test_validate_branch_issue_linkage_no_issue_number(
        self, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation fails when branch name has no issue number."""
        # Setup: Mock branch name "feature-branch" (no issue number prefix)
        mock_get_branch.return_value = "feature-branch"

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    def test_validate_branch_issue_linkage_no_branch_name(
        self, mock_get_branch: MagicMock, tmp_path: Path
    ) -> None:
        """Tests validation fails when branch name cannot be determined."""
        # Setup: Mock branch name return None
        mock_get_branch.return_value = None

        # Call: validate_branch_issue_linkage(tmp_path)
        result = validate_branch_issue_linkage(tmp_path)

        # Assert: Returns None
        assert result is None
        mock_get_branch.assert_called_once_with(tmp_path)
