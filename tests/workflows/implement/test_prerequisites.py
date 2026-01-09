"""Tests for implement workflow prerequisites checking."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from mcp_coder.workflows.implement.prerequisites import (
    check_git_clean,
    check_main_branch,
    check_prerequisites,
    has_implementation_tasks,
)


class TestCheckGitClean:
    """Test check_git_clean function."""

    @patch("mcp_coder.workflows.implement.prerequisites.is_working_directory_clean")
    def test_git_clean_success(self, mock_is_clean: MagicMock) -> None:
        """Test git clean check when working directory is clean."""
        mock_is_clean.return_value = True

        result = check_git_clean(Path("/test/project"))

        assert result is True
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )

    @patch("mcp_coder.workflows.implement.prerequisites.is_working_directory_clean")
    def test_git_clean_dirty_directory(self, mock_is_clean: MagicMock) -> None:
        """Test git clean check when working directory is dirty."""
        mock_is_clean.return_value = False

        result = check_git_clean(Path("/test/project"))

        assert result is False
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )

    @patch("mcp_coder.workflows.implement.prerequisites.get_full_status")
    @patch("mcp_coder.workflows.implement.prerequisites.is_working_directory_clean")
    def test_git_clean_dirty_with_status_details(
        self, mock_is_clean: MagicMock, mock_get_status: MagicMock
    ) -> None:
        """Test git clean check logs detailed status when dirty."""
        mock_is_clean.return_value = False
        mock_get_status.return_value = {
            "staged": ["file1.py"],
            "modified": ["file2.py"],
            "untracked": ["file3.py"],
        }

        result = check_git_clean(Path("/test/project"))

        assert result is False
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )
        mock_get_status.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.prerequisites.is_working_directory_clean")
    def test_git_clean_value_error(self, mock_is_clean: MagicMock) -> None:
        """Test git clean check handles ValueError from git operations."""
        mock_is_clean.side_effect = ValueError("Not a git repository")

        result = check_git_clean(Path("/test/project"))

        assert result is False
        mock_is_clean.assert_called_once_with(
            Path("/test/project"), ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )


class TestCheckMainBranch:
    """Test check_main_branch function."""

    @patch("mcp_coder.workflows.implement.prerequisites.get_default_branch_name")
    @patch("mcp_coder.workflows.implement.prerequisites.get_current_branch_name")
    def test_main_branch_check_success(
        self, mock_current: MagicMock, mock_default: MagicMock
    ) -> None:
        """Test main branch check when current branch is not main."""
        mock_current.return_value = "feature-branch"
        mock_default.return_value = "main"

        result = check_main_branch(Path("/test/project"))

        assert result is True
        mock_current.assert_called_once_with(Path("/test/project"))
        mock_default.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.prerequisites.get_default_branch_name")
    @patch("mcp_coder.workflows.implement.prerequisites.get_current_branch_name")
    def test_main_branch_check_on_main_branch(
        self, mock_current: MagicMock, mock_default: MagicMock
    ) -> None:
        """Test main branch check fails when current branch is main."""
        mock_current.return_value = "main"
        mock_default.return_value = "main"

        result = check_main_branch(Path("/test/project"))

        assert result is False
        mock_current.assert_called_once_with(Path("/test/project"))
        mock_default.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.prerequisites.get_current_branch_name")
    def test_main_branch_check_no_current_branch(self, mock_current: MagicMock) -> None:
        """Test main branch check fails when current branch is None."""
        mock_current.return_value = None

        result = check_main_branch(Path("/test/project"))

        assert result is False
        mock_current.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.prerequisites.get_default_branch_name")
    @patch("mcp_coder.workflows.implement.prerequisites.get_current_branch_name")
    def test_main_branch_check_no_default_branch(
        self, mock_current: MagicMock, mock_default: MagicMock
    ) -> None:
        """Test main branch check fails when default branch is None."""
        mock_current.return_value = "feature-branch"
        mock_default.return_value = None

        result = check_main_branch(Path("/test/project"))

        assert result is False
        mock_current.assert_called_once_with(Path("/test/project"))
        mock_default.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.prerequisites.get_current_branch_name")
    def test_main_branch_check_exception(self, mock_current: MagicMock) -> None:
        """Test main branch check handles exceptions."""
        mock_current.side_effect = Exception("Git error")

        result = check_main_branch(Path("/test/project"))

        assert result is False
        mock_current.assert_called_once_with(Path("/test/project"))


class TestCheckPrerequisites:
    """Test check_prerequisites function."""

    def test_prerequisites_success(self, tmp_path: Path) -> None:
        """Test prerequisites check when all conditions are met."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create pr_info/TASK_TRACKER.md file
        pr_info_dir = tmp_path / "pr_info"
        pr_info_dir.mkdir()
        task_tracker = pr_info_dir / "TASK_TRACKER.md"
        task_tracker.write_text("# Task Tracker\n\n## Tasks\n- [ ] Test task")

        result = check_prerequisites(tmp_path)

        assert result is True

    def test_prerequisites_no_git_directory(self, tmp_path: Path) -> None:
        """Test prerequisites check fails when .git directory missing."""
        result = check_prerequisites(tmp_path)

        assert result is False

    def test_prerequisites_no_task_tracker(self, tmp_path: Path) -> None:
        """Test prerequisites check fails when TASK_TRACKER.md missing."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = check_prerequisites(tmp_path)

        assert result is False

    def test_prerequisites_no_pr_info_directory(self, tmp_path: Path) -> None:
        """Test prerequisites check fails when pr_info directory missing."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = check_prerequisites(tmp_path)

        assert result is False


class TestHasImplementationTasks:
    """Test has_implementation_tasks function."""

    @patch("mcp_coder.workflows.implement.prerequisites._find_implementation_section")
    @patch("mcp_coder.workflows.implement.prerequisites._parse_task_lines")
    @patch("mcp_coder.workflows.implement.prerequisites._read_task_tracker")
    def test_has_implementation_tasks_true(
        self,
        mock_read: MagicMock,
        mock_parse: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test has_implementation_tasks returns True when tasks exist."""
        mock_read.return_value = "mock content"
        mock_find.return_value = "mock section"
        mock_parse.return_value = [
            MagicMock(name="Task 1", is_complete=False),
            MagicMock(name="Task 2", is_complete=True),
        ]

        result = has_implementation_tasks(Path("/test/project"))

        assert result is True
        mock_read.assert_called_once_with(str(Path("/test/project") / "pr_info"))
        mock_find.assert_called_once_with("mock content")
        mock_parse.assert_called_once_with("mock section")

    @patch("mcp_coder.workflows.implement.prerequisites._find_implementation_section")
    @patch("mcp_coder.workflows.implement.prerequisites._parse_task_lines")
    @patch("mcp_coder.workflows.implement.prerequisites._read_task_tracker")
    def test_has_implementation_tasks_false(
        self,
        mock_read: MagicMock,
        mock_parse: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test has_implementation_tasks returns False when no tasks exist."""
        mock_read.return_value = "mock content"
        mock_find.return_value = "mock section"
        mock_parse.return_value = []

        result = has_implementation_tasks(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflows.implement.prerequisites._read_task_tracker")
    def test_has_implementation_tasks_exception(self, mock_read: MagicMock) -> None:
        """Test has_implementation_tasks returns False on exception."""
        mock_read.side_effect = Exception("File not found")

        result = has_implementation_tasks(Path("/test/project"))

        assert result is False


class TestIntegration:
    """Integration tests combining multiple prerequisite checks."""

    def test_all_prerequisites_pass_with_mocks(self) -> None:
        """Test integration when all prerequisite checks pass using individual mocks."""
        project_dir = Path("/test/project")

        with (
            patch(
                "mcp_coder.workflows.implement.prerequisites.is_working_directory_clean",
                return_value=True,
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites.get_current_branch_name",
                return_value="feature-branch",
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites.get_default_branch_name",
                return_value="main",
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites._read_task_tracker",
                return_value="content",
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites._find_implementation_section",
                return_value="section",
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites._parse_task_lines",
                return_value=[MagicMock()],
            ),
        ):

            # Mock filesystem checks for check_prerequisites
            with patch.object(Path, "exists", return_value=True):
                # This would be the typical usage pattern
                assert check_git_clean(project_dir) is True
                assert check_main_branch(project_dir) is True
                assert check_prerequisites(project_dir) is True
                assert has_implementation_tasks(project_dir) is True

    def test_git_clean_fails_early_with_mocks(self) -> None:
        """Test early failure when git clean check fails."""
        project_dir = Path("/test/project")

        with (
            patch(
                "mcp_coder.workflows.implement.prerequisites.is_working_directory_clean",
                return_value=False,
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites.get_full_status",
                return_value={"staged": [], "modified": [], "untracked": []},
            ),
        ):

            # Git clean fails, so workflow would stop here
            assert check_git_clean(project_dir) is False

    def test_main_branch_fails_after_git_clean_passes_with_mocks(self) -> None:
        """Test failure when main branch check fails after git clean passes."""
        project_dir = Path("/test/project")

        with (
            patch(
                "mcp_coder.workflows.implement.prerequisites.is_working_directory_clean",
                return_value=True,
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites.get_current_branch_name",
                return_value="main",
            ),
            patch(
                "mcp_coder.workflows.implement.prerequisites.get_default_branch_name",
                return_value="main",
            ),
        ):

            # Git clean passes, but main branch check fails
            assert check_git_clean(project_dir) is True
            assert check_main_branch(project_dir) is False
