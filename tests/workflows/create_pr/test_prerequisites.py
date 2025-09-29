"""Tests for create_PR workflow prerequisites checking."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from workflows.create_PR import check_prerequisites


class TestCheckPrerequisites:
    """Test check_prerequisites function."""

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_prerequisites_all_pass(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check when all conditions are met."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        result = check_prerequisites(Path("/test/project"))

        assert result is True
        mock_clean.assert_called_once()
        mock_incomplete_tasks.assert_called_once()
        mock_current_branch.assert_called_once()
        mock_parent_branch.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    def test_prerequisites_dirty_working_directory(self, mock_clean: MagicMock) -> None:
        """Test prerequisites check fails when working directory is dirty."""
        mock_clean.return_value = False

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    def test_prerequisites_incomplete_tasks(
        self, mock_incomplete_tasks: MagicMock, mock_clean: MagicMock
    ) -> None:
        """Test prerequisites check fails when incomplete tasks exist."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = ["Incomplete task 1", "Incomplete task 2"]

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()
        mock_incomplete_tasks.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_prerequisites_same_branch(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check fails when current branch is parent branch."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = "main"
        mock_parent_branch.return_value = "main"

        result = check_prerequisites(Path("/test/project"))

        assert result is False

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    def test_prerequisites_no_current_branch(
        self,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check fails when current branch is unknown."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = None

        result = check_prerequisites(Path("/test/project"))

        assert result is False

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_prerequisites_no_parent_branch(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check fails when parent branch is unknown."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = None

        result = check_prerequisites(Path("/test/project"))

        assert result is False

    @patch("workflows.create_PR.is_working_directory_clean")
    def test_prerequisites_git_exception(self, mock_clean: MagicMock) -> None:
        """Test prerequisites check fails when git operations raise exceptions."""
        mock_clean.side_effect = Exception("Git error")

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    def test_prerequisites_task_tracker_exception(
        self, mock_incomplete_tasks: MagicMock, mock_clean: MagicMock
    ) -> None:
        """Test prerequisites check fails when task tracker operations raise exceptions."""
        mock_clean.return_value = True
        mock_incomplete_tasks.side_effect = Exception("Task tracker error")

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()
        mock_incomplete_tasks.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    def test_prerequisites_branch_exception(
        self,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check fails when branch operations raise exceptions."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.side_effect = Exception("Branch error")

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()
        mock_incomplete_tasks.assert_called_once()
        mock_current_branch.assert_called_once()
