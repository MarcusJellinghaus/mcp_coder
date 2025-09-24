"""Tests for task tracker parsing functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.utils.task_tracker import (
    TaskInfo,
    TaskTrackerError,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    _read_task_tracker,
)


def create_test_tracker_content(tasks: list[tuple[str, bool]]) -> str:
    """Helper to generate test markdown content.

    Args:
        tasks: List of (task_name, is_complete) tuples

    Returns:
        Formatted markdown content with tasks
    """
    content = """# Task Status Tracker

## Instructions for LLM
This tracks Feature Implementation tasks.

## Tasks

### Implementation Steps

"""
    for task_name, is_complete in tasks:
        checkbox = "[x]" if is_complete else "[ ]"
        content += f"- {checkbox} {task_name}\n"

    return content


class TestTaskInfo:
    """Test TaskInfo dataclass creation and attributes."""

    def test_task_info_creation(self):
        """Test TaskInfo dataclass creation with all attributes."""
        task = TaskInfo(
            name="Setup project structure",
            is_complete=False,
            line_number=15,
            indentation_level=0,
        )

        assert task.name == "Setup project structure"
        assert task.is_complete is False
        assert task.line_number == 15
        assert task.indentation_level == 0

    def test_task_info_completed(self):
        """Test TaskInfo with completed task."""
        task = TaskInfo(
            name="Implement parser",
            is_complete=True,
            line_number=16,
            indentation_level=1,
        )

        assert task.name == "Implement parser"
        assert task.is_complete is True
        assert task.line_number == 16
        assert task.indentation_level == 1


class TestExceptions:
    """Test exception hierarchy."""

    def test_exception_hierarchy(self):
        """Test that specific exceptions inherit from base."""
        assert issubclass(TaskTrackerFileNotFoundError, TaskTrackerError)
        assert issubclass(TaskTrackerSectionNotFoundError, TaskTrackerError)
        assert issubclass(TaskTrackerError, Exception)

    def test_exception_creation(self):
        """Test exception creation with custom messages."""
        file_error = TaskTrackerFileNotFoundError("File not found")
        section_error = TaskTrackerSectionNotFoundError("Section not found")

        assert str(file_error) == "File not found"
        assert str(section_error) == "Section not found"


class TestReadTaskTracker:
    """Test _read_task_tracker function."""

    def test_read_existing_file(self):
        """Test reading existing TASK_TRACKER.md file."""
        with TemporaryDirectory() as temp_dir:
            # Create test file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            test_content = "# Test Tracker\n\nSome content here"
            tracker_path.write_text(test_content, encoding="utf-8")

            # Test reading
            content = _read_task_tracker(temp_dir)
            assert content == test_content

    def test_read_missing_file(self):
        """Test TaskTrackerFileNotFoundError for missing TASK_TRACKER.md file."""
        with TemporaryDirectory() as temp_dir:
            # Test with empty directory
            with pytest.raises(TaskTrackerFileNotFoundError) as exc_info:
                _read_task_tracker(temp_dir)

            assert "TASK_TRACKER.md not found" in str(exc_info.value)
            assert temp_dir in str(exc_info.value)

    def test_read_utf8_encoding(self):
        """Test reading file with UTF-8 encoding."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            # Test with unicode content
            test_content = "# Test Tracker\n\n- [ ] Task with émojis 🚀"
            tracker_path.write_text(test_content, encoding="utf-8")

            content = _read_task_tracker(temp_dir)
            assert content == test_content


class TestCreateTestTrackerContent:
    """Test helper function for generating test content."""

    def test_empty_tasks(self):
        """Test generating content with no tasks."""
        content = create_test_tracker_content([])

        assert "# Task Status Tracker" in content
        assert "### Implementation Steps" in content
        # Should not contain any task lines
        assert "- [ ]" not in content
        assert "- [x]" not in content

    def test_mixed_tasks(self):
        """Test generating content with mixed complete/incomplete tasks."""
        tasks = [
            ("Setup project", False),
            ("Implement core", True),
            ("Add tests", False),
        ]

        content = create_test_tracker_content(tasks)

        assert "- [ ] Setup project" in content
        assert "- [x] Implement core" in content
        assert "- [ ] Add tests" in content

    def test_only_complete_tasks(self):
        """Test generating content with only complete tasks."""
        tasks = [("Task 1", True), ("Task 2", True)]

        content = create_test_tracker_content(tasks)

        assert "- [x] Task 1" in content
        assert "- [x] Task 2" in content
        assert "- [ ]" not in content

    def test_only_incomplete_tasks(self):
        """Test generating content with only incomplete tasks."""
        tasks = [("Task 1", False), ("Task 2", False)]

        content = create_test_tracker_content(tasks)

        assert "- [ ] Task 1" in content
        assert "- [ ] Task 2" in content
        assert "- [x]" not in content
