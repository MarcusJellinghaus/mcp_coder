"""Tests for implement workflow prerequisites checking."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_utils.task_tracker_classify import TrackerState
from mcp_coder.workflows.implement.prerequisites import (
    check_git_clean,
    check_main_branch,
    check_prerequisites,
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


class TestCheckPrerequisitesTaskTracker:
    """Tests for task tracker validation in check_prerequisites."""

    def test_fails_when_pr_info_missing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test returns False when pr_info/ folder is missing."""
        # Setup: git repo without pr_info/ dir
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Call check_prerequisites()
        result = check_prerequisites(tmp_path)

        # Assert: returns False, logs "folder pr_info not found. Run 'create_plan' first."
        assert result is False
        assert "folder pr_info not found. Run 'create_plan' first." in caplog.text

    def test_validates_existing_tracker_success(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test validation passes for valid existing tracker."""
        # Setup: git repo with valid TASK_TRACKER.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        pr_info_dir = tmp_path / "pr_info"
        pr_info_dir.mkdir()
        task_tracker = pr_info_dir / "TASK_TRACKER.md"
        # Valid tracker with required sections
        task_tracker.write_text(
            "# Task Status Tracker\n\n## Tasks\n\n- [ ] Test task\n\n## Pull Request\n"
        )

        # Call check_prerequisites() with INFO level logging captured
        with caplog.at_level(
            logging.INFO, logger="mcp_coder.workflows.implement.prerequisites"
        ):
            result = check_prerequisites(tmp_path)

        # Assert: returns True, file unchanged
        assert result is True
        assert "Prerequisites check passed" in caplog.text

    def test_invalid_tracker_warns_and_passes(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an invalid tracker logs a WARNING but passes for prep to repair."""
        # Setup: git repo with TASK_TRACKER.md missing ## Tasks header
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        pr_info_dir = tmp_path / "pr_info"
        pr_info_dir.mkdir()
        task_tracker = pr_info_dir / "TASK_TRACKER.md"
        # Invalid tracker - missing ## Tasks section
        task_tracker.write_text(
            "# Task Status Tracker\n\n"
            "Some content without proper sections\n\n"
            "## Pull Request\n"
        )

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.implement.prerequisites"
        ):
            result = check_prerequisites(tmp_path)

        assert result is True
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("Invalid task tracker structure" in r.message for r in warnings)
        assert "no '## Tasks' section" in caplog.text

    def test_missing_tracker_fails(self, tmp_path: Path) -> None:
        """Test returns False when pr_info/ exists but TASK_TRACKER.md does not."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "pr_info").mkdir()

        assert check_prerequisites(tmp_path) is False


class TestIntegration:
    """Integration tests combining multiple prerequisite checks."""

    def test_all_prerequisites_pass_with_mocks(self) -> None:
        """Test integration when all prerequisite checks pass using individual mocks."""
        project_dir = Path("/test/project")

        with (
            patch(
                "mcp_coder.workflow_steps.prerequisites.is_working_directory_clean",
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
                "mcp_coder.workflows.implement.prerequisites.classify_task_tracker",
                return_value=(TrackerState.POPULATED, []),
            ),
        ):
            # Mock filesystem checks for check_prerequisites
            with patch.object(Path, "exists", return_value=True):
                # This would be the typical usage pattern
                assert check_git_clean(project_dir) is True
                assert check_main_branch(project_dir) is True
                assert check_prerequisites(project_dir) is True

    def test_git_clean_fails_early_with_mocks(self) -> None:
        """Test early failure when git clean check fails."""
        project_dir = Path("/test/project")

        with (
            patch(
                "mcp_coder.workflow_steps.prerequisites.is_working_directory_clean",
                return_value=False,
            ),
            patch(
                "mcp_coder.workflow_steps.prerequisites.get_full_status",
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
                "mcp_coder.workflow_steps.prerequisites.is_working_directory_clean",
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
