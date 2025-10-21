"""Tests for create_PR workflow main function.

NOTE: This file tests the LEGACY workflows/create_PR.py main() function.
It will be removed in Step 5 when the legacy file is deleted.
The new run_create_pr_workflow() function in core.py will be tested via CLI tests.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workflows.create_PR import main


class TestMainWorkflow:
    """Test main workflow function."""

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.commit_all_changes")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_success(
        self,
        mock_parse_args: MagicMock,
        mock_git_push: MagicMock,
        mock_commit: MagicMock,
        mock_is_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test successful complete workflow execution."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_is_clean.return_value = False  # There are changes to commit
        mock_commit.return_value = {"success": True, "commit_hash": "abc1234"}
        mock_git_push.return_value = {"success": True}

        # Should exit with code 0
        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(0)

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_prerequisites_fail(
        self,
        mock_parse_args: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow exits when prerequisites check fails."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = False

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(1)

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_pr_creation_fails(
        self,
        mock_parse_args: MagicMock,
        mock_create_pr: MagicMock,
        mock_git_push: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow exits when PR creation fails."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_git_push.return_value = {"success": True}  # Push succeeds
        mock_create_pr.return_value = False  # PR creation fails

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(1)

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.commit_all_changes")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.logger")
    def test_main_workflow_cleanup_fails(
        self,
        mock_logger: MagicMock,
        mock_parse_args: MagicMock,
        mock_git_push: MagicMock,
        mock_commit: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow continues when cleanup fails but logs warning."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = False  # Cleanup fails
        mock_commit.return_value = {"success": True, "commit_hash": "abc1234"}
        mock_git_push.return_value = {"success": True}

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            # Should still exit successfully even if cleanup fails
            mock_exit.assert_called_once_with(0)
            # Should log warning about cleanup failure
            mock_logger.warning.assert_called()

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.commit_all_changes")
    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.logger")
    def test_main_workflow_commit_fails(
        self,
        mock_logger: MagicMock,
        mock_parse_args: MagicMock,
        mock_commit: MagicMock,
        mock_is_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow continues when commit fails but logs warning."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_is_clean.return_value = False  # There are changes to commit
        mock_commit.return_value = {"success": False, "error": "Commit failed"}

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            # Should still exit successfully even if commit fails
            mock_exit.assert_called_once_with(0)
            # Should log warning about commit failure
            mock_logger.warning.assert_called()

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.commit_all_changes")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.logger")
    def test_main_workflow_push_fails(
        self,
        mock_logger: MagicMock,
        mock_parse_args: MagicMock,
        mock_git_push: MagicMock,
        mock_commit: MagicMock,
        mock_is_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow continues when push fails but logs warning."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_is_clean.return_value = False  # There are changes to commit
        mock_commit.return_value = {"success": True, "commit_hash": "abc1234"}
        mock_git_push.return_value = {"success": False, "error": "Push failed"}

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            # Should still exit successfully even if push fails
            mock_exit.assert_called_once_with(0)
            # Should log warning about push failure
            mock_logger.warning.assert_called()

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_generate_summary_exits(
        self,
        mock_parse_args: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow when generate_pr_summary exits (e.g., LLM failure)."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.side_effect = SystemExit(1)  # Summary generation exits

        # Should propagate the SystemExit from generate_pr_summary
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.resolve_project_dir")
    def test_main_workflow_resolve_dir_exits(
        self,
        mock_resolve_dir: MagicMock,
        mock_parse_args: MagicMock,
    ) -> None:
        """Test workflow when resolve_project_dir exits (e.g., invalid directory)."""
        mock_args = MagicMock()
        mock_parse_args.return_value = mock_args
        mock_resolve_dir.side_effect = SystemExit(1)  # Directory resolution exits

        # Should propagate the SystemExit from resolve_project_dir
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.log_step")
    def test_main_workflow_no_cleanup_changes(
        self,
        mock_log_step: MagicMock,
        mock_parse_args: MagicMock,
        mock_git_push: MagicMock,
        mock_is_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow when cleanup produces no changes to commit."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_is_clean.return_value = True  # No changes to commit
        mock_git_push.return_value = {"success": True}

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(0)

        # Verify "No cleanup changes to commit" message was logged
        mock_log_step.assert_any_call("No cleanup changes to commit")
