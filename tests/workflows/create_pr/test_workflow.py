"""Tests for create_pr workflow orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import run_create_pr_workflow


class TestRunCreatePrWorkflow:
    """Test suite for run_create_pr_workflow orchestration."""

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    def test_workflow_complete_success(
        self,
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
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_clean.return_value = False  # Has changes to commit
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}

        # Execute
        result = run_create_pr_workflow(Path("/test"), "claude", "cli")

        # Verify
        assert result == 0
        mock_prereqs.assert_called_once_with(Path("/test"))
        mock_generate.assert_called_once_with(Path("/test"), "claude", "cli", None, None)
        mock_create_pr.assert_called_once_with(Path("/test"), "Test Title", "Test Body")
        mock_cleanup.assert_called_once_with(Path("/test"))
        mock_commit.assert_called_once()
        # git_push should be called twice: once after generate_pr_summary and once after commit
        assert mock_push.call_count == 2

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_workflow_prerequisites_fail(self, mock_prereqs: MagicMock) -> None:
        """Test workflow exits when prerequisites fail."""
        mock_prereqs.return_value = False

        result = run_create_pr_workflow(Path("/test"), "claude", "cli")

        assert result == 1
        mock_prereqs.assert_called_once_with(Path("/test"))

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    def test_workflow_pr_creation_fails(
        self,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
    ) -> None:
        """Test workflow exits when PR creation fails."""
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Title", "Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = False  # PR creation fails

        result = run_create_pr_workflow(Path("/test"), "claude", "cli")

        assert result == 1
        mock_create_pr.assert_called_once_with(Path("/test"), "Title", "Body")

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    def test_workflow_generate_summary_exception(
        self, mock_generate: MagicMock, mock_prereqs: MagicMock
    ) -> None:
        """Test workflow handles generate_pr_summary exceptions."""
        mock_prereqs.return_value = True
        mock_generate.side_effect = ValueError("LLM failed")

        result = run_create_pr_workflow(Path("/test"), "claude", "cli")

        assert result == 1
        mock_generate.assert_called_once_with(Path("/test"), "claude", "cli", None, None)

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    def test_workflow_execution_dir_passed_to_generate_summary(
        self,
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
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_clean.return_value = True  # Clean directory, no commit needed

        # Execute with execution_dir
        result = run_create_pr_workflow(
            tmp_path, "claude", "cli", None, exec_dir
        )

        # Verify
        assert result == 0
        # Verify execution_dir was passed to generate_pr_summary
        mock_generate.assert_called_once_with(tmp_path, "claude", "cli", None, exec_dir)
