"""Tests for create_PR workflow file operations.

Tests for delete_pr_info_directory and cleanup_repository.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.create_pr.core import (
    cleanup_repository,
    delete_pr_info_directory,
)


class TestDeletePrInfoDirectory:
    """Tests for delete_pr_info_directory function."""

    def test_deletes_entire_pr_info_directory(self) -> None:
        """Test entire pr_info/ directory is deleted with all contents."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Setup: create pr_info/ with steps/, .conversations/, TASK_TRACKER.md
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create steps/ subdirectory with files
            steps_dir = pr_info_dir / "steps"
            steps_dir.mkdir()
            (steps_dir / "step_1.md").write_text("Step 1 content")
            (steps_dir / "step_2.md").write_text("Step 2 content")

            # Create .conversations/ subdirectory
            conversations_dir = pr_info_dir / ".conversations"
            conversations_dir.mkdir()
            (conversations_dir / "log.txt").write_text("Conversation log")

            # Create files directly in pr_info/
            (pr_info_dir / "TASK_TRACKER.md").write_text("# Task Tracker")
            (pr_info_dir / "Decisions.md").write_text("# Decisions")

            # Verify setup
            assert pr_info_dir.exists()
            assert steps_dir.exists()
            assert conversations_dir.exists()
            assert (pr_info_dir / "TASK_TRACKER.md").exists()

            # Call delete_pr_info_directory()
            result = delete_pr_info_directory(project_dir)

            # Assert: pr_info/ directory no longer exists
            assert result is True
            assert not pr_info_dir.exists()

    def test_returns_true_when_directory_missing(self) -> None:
        """Test returns True when pr_info/ doesn't exist (no-op)."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Setup: temp dir without pr_info/
            assert not (project_dir / "pr_info").exists()

            # Call delete_pr_info_directory()
            result = delete_pr_info_directory(project_dir)

            # Assert: returns True (no-op is success)
            assert result is True

    def test_returns_true_on_successful_deletion(self) -> None:
        """Test returns True when deletion succeeds."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Setup: create pr_info/ with files
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()
            (pr_info_dir / "TASK_TRACKER.md").write_text("# Task Tracker")

            # Call delete_pr_info_directory()
            result = delete_pr_info_directory(project_dir)

            # Assert: returns True and directory is deleted
            assert result is True
            assert not pr_info_dir.exists()

    @patch("mcp_coder.workflows.create_pr.core.logger")
    def test_returns_false_on_permission_error(self, mock_logger: MagicMock) -> None:
        """Test returns False on permission error."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create pr_info/ directory
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()
            (pr_info_dir / "file.txt").write_text("content")

            # Mock shutil.rmtree to simulate permission error
            with patch(
                "mcp_coder.workflows.create_pr.core.shutil.rmtree"
            ) as mock_rmtree:
                mock_rmtree.side_effect = PermissionError("Access denied")

                # Call delete_pr_info_directory()
                result = delete_pr_info_directory(project_dir)

                # Assert: returns False on error
                assert result is False

                # Should log error
                mock_logger.error.assert_called()

    @patch("mcp_coder.workflows.create_pr.core.logger")
    def test_logs_info_on_successful_deletion(self, mock_logger: MagicMock) -> None:
        """Test that successful deletion is logged."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create and delete directory
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()
            (pr_info_dir / "file.txt").write_text("content")

            result = delete_pr_info_directory(project_dir)
            assert result is True

            # Should log the operation
            mock_logger.info.assert_called()


class TestCleanupRepositorySimplified:
    """Tests for simplified cleanup_repository function.

    The simplified cleanup_repository() should:
    1. Delete the entire pr_info/ directory using delete_pr_info_directory()
    2. Clean profiler output using clean_profiler_output()
    """

    def test_calls_delete_pr_info_directory(self) -> None:
        """Test cleanup_repository deletes pr_info/ directory."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Setup: create pr_info/ with content
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create steps/ subdirectory
            steps_dir = pr_info_dir / "steps"
            steps_dir.mkdir()
            (steps_dir / "step_1.md").write_text("Step 1")

            # Create .conversations/ subdirectory
            conversations_dir = pr_info_dir / ".conversations"
            conversations_dir.mkdir()
            (conversations_dir / "log.txt").write_text("Log")

            # Create TASK_TRACKER.md
            (pr_info_dir / "TASK_TRACKER.md").write_text("# Tracker")

            # Verify setup
            assert pr_info_dir.exists()

            # Call cleanup_repository()
            result = cleanup_repository(project_dir)

            # Assert: pr_info/ deleted, returns True
            assert result is True
            assert not pr_info_dir.exists()

    def test_still_cleans_profiler_output(self) -> None:
        """Test cleanup_repository still cleans profiler output."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Setup: create docs/tests/performance_data/prof/ with files
            prof_dir = project_dir / "docs" / "tests" / "performance_data" / "prof"
            prof_dir.mkdir(parents=True)
            (prof_dir / "test1.prof").write_text("profiler data 1")
            (prof_dir / "test2.prof").write_text("profiler data 2")

            # Verify setup
            assert (prof_dir / "test1.prof").exists()
            assert (prof_dir / "test2.prof").exists()

            # Call cleanup_repository()
            result = cleanup_repository(project_dir)

            # Assert: prof/ files deleted but directory preserved
            assert result is True
            assert prof_dir.exists()  # Directory still exists
            assert not (prof_dir / "test1.prof").exists()  # Files removed
            assert not (prof_dir / "test2.prof").exists()

    def test_handles_both_cleanup_tasks(self) -> None:
        """Test cleanup_repository handles both pr_info/ and profiler cleanup."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Setup: create pr_info/ with content
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()
            (pr_info_dir / "TASK_TRACKER.md").write_text("# Tracker")

            # Setup: create profiler output
            prof_dir = project_dir / "docs" / "tests" / "performance_data" / "prof"
            prof_dir.mkdir(parents=True)
            (prof_dir / "test.prof").write_text("profiler data")

            # Call cleanup_repository()
            result = cleanup_repository(project_dir)

            # Assert: both cleaned
            assert result is True
            assert not pr_info_dir.exists()  # pr_info/ deleted
            assert prof_dir.exists()  # prof/ directory exists
            assert not (prof_dir / "test.prof").exists()  # prof files deleted

    def test_returns_true_when_nothing_to_clean(self) -> None:
        """Test cleanup_repository returns True when no directories exist."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # No pr_info/ or prof/ directories
            assert not (project_dir / "pr_info").exists()

            # Call cleanup_repository()
            result = cleanup_repository(project_dir)

            # Assert: success (no-op)
            assert result is True

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    def test_returns_false_when_clean_profiler_fails(
        self, mock_clean_profiler: MagicMock
    ) -> None:
        """Test cleanup_repository returns False when clean_profiler_output fails."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Mock clean_profiler_output to fail
            mock_clean_profiler.return_value = False

            # Call cleanup_repository()
            result = cleanup_repository(project_dir)

            # Assert: returns False due to failure
            assert result is False
            mock_clean_profiler.assert_called_once_with(project_dir)
