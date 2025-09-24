"""Tests for task tracker parsing functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.utils.task_tracker import (
    TaskInfo,
    TaskTrackerError,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    _find_implementation_section,
    _parse_task_lines,
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

    def test_task_info_creation(self) -> None:
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

    def test_task_info_completed(self) -> None:
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

    def test_exception_hierarchy(self) -> None:
        """Test that specific exceptions inherit from base."""
        assert issubclass(TaskTrackerFileNotFoundError, TaskTrackerError)
        assert issubclass(TaskTrackerSectionNotFoundError, TaskTrackerError)
        assert issubclass(TaskTrackerError, Exception)

    def test_exception_creation(self) -> None:
        """Test exception creation with custom messages."""
        file_error = TaskTrackerFileNotFoundError("File not found")
        section_error = TaskTrackerSectionNotFoundError("Section not found")

        assert str(file_error) == "File not found"
        assert str(section_error) == "Section not found"


class TestReadTaskTracker:
    """Test _read_task_tracker function."""

    def test_read_existing_file(self) -> None:
        """Test reading existing TASK_TRACKER.md file."""
        with TemporaryDirectory() as temp_dir:
            # Create test file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            test_content = "# Test Tracker\n\nSome content here"
            tracker_path.write_text(test_content, encoding="utf-8")

            # Test reading
            content = _read_task_tracker(temp_dir)
            assert content == test_content

    def test_read_missing_file(self) -> None:
        """Test TaskTrackerFileNotFoundError for missing TASK_TRACKER.md file."""
        with TemporaryDirectory() as temp_dir:
            # Test with empty directory
            with pytest.raises(TaskTrackerFileNotFoundError) as exc_info:
                _read_task_tracker(temp_dir)

            assert "TASK_TRACKER.md not found" in str(exc_info.value)
            assert temp_dir in str(exc_info.value)

    def test_read_utf8_encoding(self) -> None:
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

    def test_empty_tasks(self) -> None:
        """Test generating content with no tasks."""
        content = create_test_tracker_content([])

        assert "# Task Status Tracker" in content
        assert "### Implementation Steps" in content
        # Should not contain any task lines
        assert "- [ ]" not in content
        assert "- [x]" not in content


class TestFindImplementationSection:
    """Test _find_implementation_section function."""

    def test_find_basic_section(self) -> None:
        """Test finding basic Implementation Steps section."""
        content = """# Task Tracker

## Instructions
Some instructions here.

## Tasks

### Implementation Steps

- [ ] Task 1
- [x] Task 2

### Pull Request

- [ ] Create PR
"""
        result = _find_implementation_section(content)
        assert "- [ ] Task 1" in result
        assert "- [x] Task 2" in result
        assert "- [ ] Create PR" not in result

    def test_find_case_insensitive_header(self) -> None:
        """Test case-insensitive header matching."""
        content = """# Task Tracker

### implementation steps

- [ ] Task with lowercase
- [X] Task with uppercase marker
"""
        result = _find_implementation_section(content)
        assert "- [ ] Task with lowercase" in result
        assert "- [X] Task with uppercase marker" in result

    def test_find_uppercase_header(self) -> None:
        """Test uppercase header matching."""
        content = """# Task Tracker

### IMPLEMENTATION STEPS

- [x] Task with uppercase header
- [ ] Another task
"""
        result = _find_implementation_section(content)
        assert "- [x] Task with uppercase header" in result
        assert "- [ ] Another task" in result

    def test_section_not_found(self) -> None:
        """Test TaskTrackerSectionNotFoundError when section missing."""
        content = """# Task Tracker

## Some Other Section

- [ ] Not an implementation step
"""
        with pytest.raises(TaskTrackerSectionNotFoundError) as exc_info:
            _find_implementation_section(content)
        assert "Implementation Steps section not found" in str(exc_info.value)

    def test_stop_at_pull_request(self) -> None:
        """Test that parsing stops at Pull Request section."""
        content = """# Task Tracker

### Implementation Steps

- [ ] Implementation task
- [x] Another impl task

### Pull Request

- [ ] PR task should be excluded
- [ ] Another PR task

### More Content

- [ ] This should also be excluded
"""
        result = _find_implementation_section(content)
        assert "- [ ] Implementation task" in result
        assert "- [x] Another impl task" in result
        assert "- [ ] PR task should be excluded" not in result
        assert "- [ ] Another PR task" not in result
        assert "- [ ] This should also be excluded" not in result


class TestParseTaskLines:
    """Test _parse_task_lines function."""

    def test_parse_mixed_status_tasks(self) -> None:
        """Test parsing lines with both complete and incomplete tasks."""
        section_content = """- [ ] **Step 1: Setup Data Models** - [step_1.md](steps/step_1.md)
  - [ ] Create package structure
  - [x] Define TaskInfo dataclass
  - [ ] Implement exception hierarchy

- [x] **Step 2: Core Parser** - [step_2.md](steps/step_2.md)
  - [x] Implement section parsing
  - [x] Add task extraction logic
"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 7

        # Check top-level tasks
        assert tasks[0].name == "Step 1: Setup Data Models"
        assert tasks[0].is_complete is False
        assert tasks[0].line_number == 1
        assert tasks[0].indentation_level == 0

        assert tasks[4].name == "Step 2: Core Parser"
        assert tasks[4].is_complete is True
        assert tasks[4].line_number == 5
        assert tasks[4].indentation_level == 0

        # Check indented tasks
        assert tasks[1].name == "Create package structure"
        assert tasks[1].is_complete is False
        assert tasks[1].line_number == 2
        assert tasks[1].indentation_level == 1

        assert tasks[2].name == "Define TaskInfo dataclass"
        assert tasks[2].is_complete is True
        assert tasks[2].line_number == 3
        assert tasks[2].indentation_level == 1

        # Check remaining tasks
        assert tasks[3].name == "Implement exception hierarchy"
        assert tasks[3].is_complete is False
        assert tasks[3].line_number == 4
        assert tasks[3].indentation_level == 1

        assert tasks[5].name == "Implement section parsing"
        assert tasks[5].is_complete is True
        assert tasks[5].line_number == 6
        assert tasks[5].indentation_level == 1

        assert tasks[6].name == "Add task extraction logic"
        assert tasks[6].is_complete is True
        assert tasks[6].line_number == 7
        assert tasks[6].indentation_level == 1

    def test_parse_various_checkbox_formats(self) -> None:
        """Test parsing with different checkbox formats."""
        section_content = """- [ ] Task with empty checkbox
- [x] Task with lowercase x
- [X] Task with uppercase X
- [] Malformed checkbox
- [y] Invalid checkbox marker
"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 3  # Only valid checkboxes should be parsed

        assert tasks[0].name == "Task with empty checkbox"
        assert tasks[0].is_complete is False

        assert tasks[1].name == "Task with lowercase x"
        assert tasks[1].is_complete is True

        assert tasks[2].name == "Task with uppercase X"
        assert tasks[2].is_complete is True

    def test_parse_clean_task_names(self) -> None:
        """Test that task names are cleaned of markdown formatting."""
        section_content = """- [ ] **Step 1: Bold task** - [link](file.md)
- [x] *Italic task* with extra   spaces
- [ ] Normal task name
  - [ ] **Sub-task** - [another_link](sub.md)
"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 4

        # Names should be cleaned of markdown formatting and links
        assert tasks[0].name == "Step 1: Bold task"
        assert tasks[1].name == "Italic task with extra spaces"
        assert tasks[2].name == "Normal task name"
        assert tasks[3].name == "Sub-task"

    def test_parse_empty_content(self) -> None:
        """Test parsing empty or whitespace-only content."""
        assert _parse_task_lines("") == []
        assert _parse_task_lines("   \n  \n") == []
        assert _parse_task_lines("No task lines here\nJust regular text") == []

    def test_parse_indentation_levels(self) -> None:
        """Test correct indentation level detection."""
        section_content = """- [ ] Top level task
  - [ ] First indent
    - [x] Second indent
      - [ ] Third indent
- [x] Another top level
"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 5

        assert tasks[0].indentation_level == 0
        assert tasks[1].indentation_level == 1
        assert tasks[2].indentation_level == 2
        assert tasks[3].indentation_level == 3
        assert tasks[4].indentation_level == 0

    def test_mixed_tasks(self) -> None:
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

    def test_only_complete_tasks(self) -> None:
        """Test generating content with only complete tasks."""
        tasks = [("Task 1", True), ("Task 2", True)]

        content = create_test_tracker_content(tasks)

        assert "- [x] Task 1" in content
        assert "- [x] Task 2" in content
        assert "- [ ]" not in content

    def test_only_incomplete_tasks(self) -> None:
        """Test generating content with only incomplete tasks."""
        tasks = [("Task 1", False), ("Task 2", False)]

        content = create_test_tracker_content(tasks)

        assert "- [ ] Task 1" in content
        assert "- [ ] Task 2" in content
        assert "- [x]" not in content
