"""Tests for create_plan workflow branch management functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workflows.create_plan import manage_branch, verify_steps_directory


class TestManageBranch:
    """Test manage_branch function."""

    def test_manage_branch_existing_branch(self, tmp_path: Path) -> None:
        """Test manage_branch with existing linked branch."""
        # Mock IssueBranchManager to return existing branch
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.return_value = ["123-test-feature"]
            mock_manager_class.return_value = mock_manager

            # Mock checkout_branch to succeed
            with patch("workflows.create_plan.checkout_branch", return_value=True):
                branch_name = manage_branch(tmp_path, 123, "Test Feature")

        assert branch_name == "123-test-feature"
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager.create_remote_branch_for_issue.assert_not_called()

    def test_manage_branch_create_new_branch(self, tmp_path: Path) -> None:
        """Test manage_branch creates new branch when none exist."""
        # Mock IssueBranchManager with no existing branches
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.return_value = []
            mock_manager.create_remote_branch_for_issue.return_value = {
                "success": True,
                "branch_name": "123-test-feature",
                "error": None,
                "existing_branches": [],
            }
            mock_manager_class.return_value = mock_manager

            # Mock checkout_branch to succeed
            with patch("workflows.create_plan.checkout_branch", return_value=True):
                branch_name = manage_branch(tmp_path, 123, "Test Feature")

        assert branch_name == "123-test-feature"
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager.create_remote_branch_for_issue.assert_called_once_with(123)

    def test_manage_branch_create_failure(self, tmp_path: Path) -> None:
        """Test manage_branch when branch creation fails."""
        # Mock IssueBranchManager with no existing branches
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.return_value = []
            mock_manager.create_remote_branch_for_issue.return_value = {
                "success": False,
                "branch_name": "",
                "error": "GitHub API error",
                "existing_branches": [],
            }
            mock_manager_class.return_value = mock_manager

            branch_name = manage_branch(tmp_path, 123, "Test Feature")

        assert branch_name is None
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager.create_remote_branch_for_issue.assert_called_once_with(123)

    def test_manage_branch_checkout_failure(self, tmp_path: Path) -> None:
        """Test manage_branch when checkout fails."""
        # Mock IssueBranchManager to return existing branch
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.return_value = ["123-test-feature"]
            mock_manager_class.return_value = mock_manager

            # Mock checkout_branch to fail
            with patch("workflows.create_plan.checkout_branch", return_value=False):
                branch_name = manage_branch(tmp_path, 123, "Test Feature")

        assert branch_name is None
        mock_manager.get_linked_branches.assert_called_once_with(123)

    def test_manage_branch_manager_initialization_error(self, tmp_path: Path) -> None:
        """Test manage_branch when IssueBranchManager initialization fails."""
        # Mock IssueBranchManager initialization to raise exception
        with patch(
            "workflows.create_plan.IssueBranchManager",
            side_effect=ValueError("Invalid configuration"),
        ):
            branch_name = manage_branch(tmp_path, 123, "Test Feature")

        assert branch_name is None

    def test_manage_branch_get_linked_branches_error(self, tmp_path: Path) -> None:
        """Test manage_branch when get_linked_branches throws error."""
        # Mock IssueBranchManager with get_linked_branches raising exception
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.side_effect = Exception("API error")
            mock_manager_class.return_value = mock_manager

            branch_name = manage_branch(tmp_path, 123, "Test Feature")

        assert branch_name is None
        mock_manager.get_linked_branches.assert_called_once_with(123)

    def test_manage_branch_logs_existing_branch(self, tmp_path: Path) -> None:
        """Test manage_branch logs when using existing branch."""
        # Mock IssueBranchManager to return existing branch
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.return_value = ["123-existing-branch"]
            mock_manager_class.return_value = mock_manager

            # Mock checkout_branch to succeed
            with patch("workflows.create_plan.checkout_branch", return_value=True):
                # Capture logger output
                with patch("workflows.create_plan.logger") as mock_logger:
                    branch_name = manage_branch(tmp_path, 123, "Test Feature")

                    # Verify logging calls
                    assert mock_logger.info.call_count >= 3
                    log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    assert any("Managing branch" in call for call in log_calls)
                    assert any(
                        "Using existing linked branch" in call for call in log_calls
                    )
                    assert any("Switched to branch" in call for call in log_calls)

        assert branch_name == "123-existing-branch"

    def test_manage_branch_logs_new_branch(self, tmp_path: Path) -> None:
        """Test manage_branch logs when creating new branch."""
        # Mock IssueBranchManager with no existing branches
        with patch("workflows.create_plan.IssueBranchManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_linked_branches.return_value = []
            mock_manager.create_remote_branch_for_issue.return_value = {
                "success": True,
                "branch_name": "123-new-branch",
                "error": None,
                "existing_branches": [],
            }
            mock_manager_class.return_value = mock_manager

            # Mock checkout_branch to succeed
            with patch("workflows.create_plan.checkout_branch", return_value=True):
                # Capture logger output
                with patch("workflows.create_plan.logger") as mock_logger:
                    branch_name = manage_branch(tmp_path, 123, "Test Feature")

                    # Verify logging calls
                    log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    assert any("Managing branch" in call for call in log_calls)
                    assert any("Created new branch" in call for call in log_calls)
                    assert any("Switched to branch" in call for call in log_calls)

        assert branch_name == "123-new-branch"


class TestVerifyStepsDirectory:
    """Test verify_steps_directory function."""

    def test_verify_steps_directory_not_exists(self, tmp_path: Path) -> None:
        """Test verify_steps_directory when directory doesn't exist."""
        result = verify_steps_directory(tmp_path)
        assert result is True

    def test_verify_steps_directory_empty(self, tmp_path: Path) -> None:
        """Test verify_steps_directory when directory is empty."""
        # Create empty pr_info/steps directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        result = verify_steps_directory(tmp_path)
        assert result is True

    def test_verify_steps_directory_has_files(self, tmp_path: Path) -> None:
        """Test verify_steps_directory when directory contains files."""
        # Create pr_info/steps directory with files
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)
        (steps_dir / "step_1.md").write_text("Step 1 content")
        (steps_dir / "step_2.md").write_text("Step 2 content")

        result = verify_steps_directory(tmp_path)
        assert result is False

    def test_verify_steps_directory_has_single_file(self, tmp_path: Path) -> None:
        """Test verify_steps_directory with single file in directory."""
        # Create pr_info/steps directory with one file
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)
        (steps_dir / "readme.md").write_text("Readme content")

        result = verify_steps_directory(tmp_path)
        assert result is False

    def test_verify_steps_directory_has_subdirectory(self, tmp_path: Path) -> None:
        """Test verify_steps_directory when directory contains subdirectory."""
        # Create pr_info/steps directory with subdirectory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)
        (steps_dir / "subdir").mkdir()

        result = verify_steps_directory(tmp_path)
        assert result is False

    def test_verify_steps_directory_logs_error_with_file_list(
        self, tmp_path: Path
    ) -> None:
        """Test verify_steps_directory logs error with file list."""
        # Create pr_info/steps directory with multiple files
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)
        (steps_dir / "step_1.md").write_text("Step 1")
        (steps_dir / "step_2.md").write_text("Step 2")
        (steps_dir / "summary.md").write_text("Summary")

        # Capture logger output
        with patch("workflows.create_plan.logger") as mock_logger:
            result = verify_steps_directory(tmp_path)

            # Verify error logging calls
            assert mock_logger.error.call_count >= 1
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            assert any("contains files" in call for call in error_calls)
            # Verify file names are logged
            assert any(
                "step_1.md" in str(call) for call in mock_logger.error.call_args_list
            )
            assert any(
                "step_2.md" in str(call) for call in mock_logger.error.call_args_list
            )
            assert any(
                "summary.md" in str(call) for call in mock_logger.error.call_args_list
            )

        assert result is False

    def test_verify_steps_directory_logs_debug_when_ok(self, tmp_path: Path) -> None:
        """Test verify_steps_directory logs debug message when directory is OK."""
        # Test with non-existent directory
        with patch("workflows.create_plan.logger") as mock_logger:
            result = verify_steps_directory(tmp_path)

            # Verify debug logging
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("does not exist" in call for call in debug_calls)

        assert result is True

        # Test with empty directory
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        with patch("workflows.create_plan.logger") as mock_logger:
            result = verify_steps_directory(tmp_path)

            # Verify debug logging
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("is empty" in call for call in debug_calls)

        assert result is True

    def test_verify_steps_directory_pr_info_exists_but_no_steps(
        self, tmp_path: Path
    ) -> None:
        """Test verify_steps_directory when pr_info exists but steps doesn't."""
        # Create pr_info directory but not steps
        pr_info_dir = tmp_path / "pr_info"
        pr_info_dir.mkdir(parents=True)

        result = verify_steps_directory(tmp_path)
        assert result is True

    def test_verify_steps_directory_with_hidden_files(self, tmp_path: Path) -> None:
        """Test verify_steps_directory with hidden files in directory."""
        # Create pr_info/steps directory with hidden file
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)
        (steps_dir / ".gitkeep").write_text("")

        result = verify_steps_directory(tmp_path)
        # Should return False because .gitkeep is still a file
        assert result is False
