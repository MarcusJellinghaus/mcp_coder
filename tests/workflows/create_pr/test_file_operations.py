"""Tests for create_PR workflow file operations (delete_steps_directory, truncate_task_tracker)."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import (
    delete_steps_directory,
    truncate_task_tracker,
)


class TestDeleteStepsDirectory:
    """Test delete_steps_directory function."""

    def test_delete_existing_directory(self) -> None:
        """Test successful deletion of existing pr_info/steps directory."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create pr_info/steps directory with some content
            steps_dir = project_dir / "pr_info" / "steps"
            steps_dir.mkdir(parents=True)

            # Add some test files
            (steps_dir / "step_1.md").write_text("Step 1 content")
            (steps_dir / "step_2.md").write_text("Step 2 content")

            # Create subdirectory with file
            sub_dir = steps_dir / "archived"
            sub_dir.mkdir()
            (sub_dir / "old_step.md").write_text("Old content")

            # Verify directory exists
            assert steps_dir.exists()
            assert (steps_dir / "step_1.md").exists()

            # Delete the directory
            result = delete_steps_directory(project_dir)

            # Verify deletion
            assert result is True
            assert not steps_dir.exists()

    def test_delete_missing_directory(self) -> None:
        """Test handling of missing pr_info/steps directory."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Ensure pr_info exists but not steps subdirectory
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            steps_dir = pr_info_dir / "steps"
            assert not steps_dir.exists()

            # Should return True (no-op for missing directory)
            result = delete_steps_directory(project_dir)
            assert result is True

    def test_delete_missing_pr_info(self) -> None:
        """Test handling when pr_info directory doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # No pr_info directory at all
            assert not (project_dir / "pr_info").exists()

            # Should return True (no-op)
            result = delete_steps_directory(project_dir)
            assert result is True

    @patch("mcp_coder.workflows.create_pr.core.logger")
    def test_delete_with_permission_error(self, mock_logger: MagicMock) -> None:
        """Test handling of permission errors during deletion."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create directory
            steps_dir = project_dir / "pr_info" / "steps"
            steps_dir.mkdir(parents=True)

            # Mock shutil.rmtree only for the actual call, not for cleanup
            with patch(
                "mcp_coder.workflows.create_pr.core.shutil.rmtree"
            ) as mock_rmtree:
                # Simulate permission error
                mock_rmtree.side_effect = PermissionError("Access denied")

                # Should return False on error
                result = delete_steps_directory(project_dir)
                assert result is False

                # Should log error
                mock_logger.error.assert_called()

    @patch("mcp_coder.workflows.create_pr.core.logger")
    def test_delete_with_logging(self, mock_logger: MagicMock) -> None:
        """Test that operations are properly logged."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create and delete directory
            steps_dir = project_dir / "pr_info" / "steps"
            steps_dir.mkdir(parents=True)

            result = delete_steps_directory(project_dir)
            assert result is True

            # Should log the operation
            mock_logger.info.assert_called()


class TestTruncateTaskTracker:
    """Test truncate_task_tracker function."""

    def test_truncate_at_tasks_section(self) -> None:
        """Test truncating TASK_TRACKER.md at '## Tasks' section."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create TASK_TRACKER.md with content
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            original_content = """# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Step 1: Setup
- [x] Task 1
- [ ] Task 2

### Step 2: Implementation
- [ ] Task 3
"""
            tracker_path.write_text(original_content, encoding="utf-8")

            # Truncate the file
            result = truncate_task_tracker(project_dir)
            assert result is True

            # Check truncated content
            truncated_content = tracker_path.read_text(encoding="utf-8")

            # Should keep everything before "## Tasks"
            assert "# Task Status Tracker" in truncated_content
            assert "## Instructions for LLM" in truncated_content
            assert "**Development Process:**" in truncated_content
            assert "---" in truncated_content

            # Should add "## Tasks" section but no task content
            assert truncated_content.strip().endswith("## Tasks")

            # Should not have any task content
            assert "### Step 1: Setup" not in truncated_content
            assert "- [x] Task 1" not in truncated_content
            assert "- [ ] Task 2" not in truncated_content

    def test_truncate_missing_tasks_section(self) -> None:
        """Test handling when '## Tasks' section is missing."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create TASK_TRACKER.md without Tasks section
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            original_content = """# Task Status Tracker

## Instructions for LLM

Some content here without Tasks section.
"""
            tracker_path.write_text(original_content, encoding="utf-8")

            # Should handle gracefully
            result = truncate_task_tracker(project_dir)
            assert result is True

            # Content should be unchanged but with ## Tasks added
            truncated_content = tracker_path.read_text(encoding="utf-8")
            assert "# Task Status Tracker" in truncated_content
            assert "## Instructions for LLM" in truncated_content
            assert "Some content here without Tasks section." in truncated_content
            assert truncated_content.strip().endswith("## Tasks")

    def test_truncate_missing_file(self) -> None:
        """Test handling of missing TASK_TRACKER.md file."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create pr_info but no TASK_TRACKER.md
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            assert not tracker_path.exists()

            # Should return False
            result = truncate_task_tracker(project_dir)
            assert result is False

    def test_truncate_missing_pr_info(self) -> None:
        """Test handling when pr_info directory doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # No pr_info directory
            assert not (project_dir / "pr_info").exists()

            # Should return False
            result = truncate_task_tracker(project_dir)
            assert result is False

    @patch("mcp_coder.workflows.create_pr.core.logger")
    def test_truncate_with_logging(self, mock_logger: MagicMock) -> None:
        """Test that operations are properly logged."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create and truncate file
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            tracker_path.write_text(
                "# Header\n\n## Tasks\n\nSome tasks", encoding="utf-8"
            )

            result = truncate_task_tracker(project_dir)
            assert result is True

            # Should log the operation
            mock_logger.info.assert_called()

    def test_truncate_preserves_whitespace(self) -> None:
        """Test that truncation preserves original whitespace and formatting."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create file with specific whitespace
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            original_content = """# Task Status Tracker

## Instructions for LLM

Content with specific formatting.

---

## Tasks

Task content to remove.
"""
            tracker_path.write_text(original_content, encoding="utf-8")

            # Truncate
            result = truncate_task_tracker(project_dir)
            assert result is True

            # Check whitespace is preserved
            truncated = tracker_path.read_text(encoding="utf-8")
            expected = """# Task Status Tracker

## Instructions for LLM

Content with specific formatting.

---

## Tasks"""
            assert truncated == expected

    @patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied"))
    @patch("mcp_coder.workflows.create_pr.core.logger")
    def test_truncate_with_permission_error(
        self, mock_logger: MagicMock, mock_read_text: MagicMock
    ) -> None:
        """Test handling of permission errors during file operations."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create file
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            tracker_path.write_text("# Content", encoding="utf-8")

            # Should return False on error
            result = truncate_task_tracker(project_dir)
            assert result is False

            # Should log error
            mock_logger.error.assert_called()
