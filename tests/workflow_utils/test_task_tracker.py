"""Tests for task tracker parsing functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TaskInfo,
    TaskTrackerError,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    _find_implementation_section,
    _get_incomplete_tasks,
    _read_task_tracker,
    get_step_progress,
)

# Multi-phase test data (realistic example)
# Note: Using ASCII-safe markers instead of emoji for Windows compatibility
MULTI_PHASE_CONTENT = """# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

---

## Tasks

## Phase 1: Initial Implementation (Steps 1-2) [COMPLETE]

### Step 1: Setup Infrastructure
- [x] Create directory structure
- [x] Add configuration files
- [x] Run quality checks

### Step 2: Core Implementation  
- [x] Implement main logic
- [x] Add error handling

---

## Phase 2: Code Review Fixes (Steps 3-4) [NEW]

### Step 3: Fix Documentation
- [ ] Update README with examples
- [ ] Add inline code comments
- [x] Fix typos in docstrings

### Step 4: Clean Up Code
- [ ] Remove unused imports
- [ ] Simplify complex functions

---

## Pull Request

- [ ] Review all changes
- [ ] Create pull request
"""


def create_test_tracker_content(
    tasks: list[tuple[str, bool]], use_dashes: bool = True
) -> str:
    """Helper to generate test markdown content.

    Args:
        tasks: List of (task_name, is_complete) tuples
        use_dashes: If True, use '- [ ]' format; if False, use '[ ]' format

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
        if use_dashes:
            content += f"- {checkbox} {task_name}\n"
        else:
            content += f"{checkbox} {task_name}\n"

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


class TestMultiPhaseTaskTracker:
    """Tests for multi-phase task tracker parsing."""

    def test_find_implementation_section_includes_all_phases(self) -> None:
        """Test that _find_implementation_section includes content from all phases."""
        section = _find_implementation_section(MULTI_PHASE_CONTENT)

        # Should include content from both phases
        assert "Phase 1" in section or "Step 1" in section
        assert "Phase 2" in section or "Step 3" in section
        assert "Update README with examples" in section
        # Should NOT include Pull Request section
        assert "Review all changes" not in section

    def test_get_incomplete_tasks_across_phases(self) -> None:
        """Test getting incomplete tasks from multiple phases."""
        # Use internal function with content string
        incomplete = _get_incomplete_tasks(MULTI_PHASE_CONTENT)

        # Should find incomplete tasks from Phase 2
        assert "Update README with examples" in incomplete
        assert "Add inline code comments" in incomplete
        assert "Remove unused imports" in incomplete
        assert "Simplify complex functions" in incomplete

        # Should NOT include completed tasks
        assert "Create directory structure" not in incomplete
        assert "Fix typos in docstrings" not in incomplete

        # Should NOT include Pull Request tasks
        assert "Review all changes" not in incomplete
        assert "Create pull request" not in incomplete

    def test_get_step_progress_includes_all_phases(self) -> None:
        """Test that get_step_progress returns steps from all phases."""
        with TemporaryDirectory() as temp_dir:
            # Write inline test data to temp directory
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            tracker_path.write_text(MULTI_PHASE_CONTENT, encoding="utf-8")

            progress = get_step_progress(temp_dir)

            # Should have steps from both phases
            step_names = list(progress.keys())
            assert any("Step 1" in name for name in step_names)
            assert any("Step 3" in name or "Step 4" in name for name in step_names)

    def test_phase_headers_recognized_as_continuations(self) -> None:
        """Test that phase headers don't terminate section parsing."""
        content = """# Task Tracker

## Tasks

## Phase 1: Done [COMPLETE]
- [x] Task from phase 1

## Phase 2: In Progress
- [ ] Task from phase 2

## Pull Request
- [ ] PR task
"""
        section = _find_implementation_section(content)

        # Phase 2 content should be included
        assert "Task from phase 2" in section
        # PR section should be excluded
        assert "PR task" not in section

    def test_backward_compatibility_single_phase(self) -> None:
        """Test that single-phase trackers still work correctly."""
        content = """# Task Tracker

## Tasks

### Step 1: Setup
- [x] Complete task
- [ ] Incomplete task

## Pull Request
- [ ] Create PR
"""
        incomplete = _get_incomplete_tasks(content)

        assert incomplete == ["Incomplete task"]
