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
    _normalize_task_name,
    _parse_task_lines,
    _read_task_tracker,
    get_incomplete_tasks,
    get_step_progress,
    has_incomplete_work,
    is_task_done,
)


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
        assert "Implementation Steps or Tasks section not found" in str(exc_info.value)

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
        assert tasks[4].line_number == 6  # Fixed: account for empty line
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
        assert tasks[5].line_number == 7  # Fixed: account for empty line
        assert tasks[5].indentation_level == 1

        assert tasks[6].name == "Add task extraction logic"
        assert tasks[6].is_complete is True
        assert tasks[6].line_number == 8  # Fixed: account for empty line
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

    def test_parse_tasks_without_dashes(self) -> None:
        """Test parsing tasks that start with [ ] instead of - [ ]."""
        section_content = """[ ] Task without dash - incomplete
[x] Task without dash - complete
[X] Task without dash - complete uppercase
[] Invalid task without dash
[y] Invalid marker without dash
"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 3  # Only valid checkboxes should be parsed

        assert tasks[0].name == "Task without dash - incomplete"
        assert tasks[0].is_complete is False
        assert tasks[0].line_number == 1
        assert tasks[0].indentation_level == 0

        assert tasks[1].name == "Task without dash - complete"
        assert tasks[1].is_complete is True
        assert tasks[1].line_number == 2
        assert tasks[1].indentation_level == 0

        assert tasks[2].name == "Task without dash - complete uppercase"
        assert tasks[2].is_complete is True
        assert tasks[2].line_number == 3
        assert tasks[2].indentation_level == 0

    def test_parse_mixed_dash_no_dash_formats(self) -> None:
        """Test parsing files with both - [ ] and [ ] formats mixed together."""
        section_content = """- [ ] Traditional task with dash
[ ] Modern task without dash
  - [x] Indented traditional task
  [x] Indented modern task
- [X] Complete traditional task
[X] Complete modern task
"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 6  # All should be parsed

        # Check traditional format tasks
        assert tasks[0].name == "Traditional task with dash"
        assert tasks[0].is_complete is False
        assert tasks[0].indentation_level == 0

        # Check modern format tasks
        assert tasks[1].name == "Modern task without dash"
        assert tasks[1].is_complete is False
        assert tasks[1].indentation_level == 0

        # Check indented tasks (both formats)
        assert tasks[2].name == "Indented traditional task"
        assert tasks[2].is_complete is True
        assert tasks[2].indentation_level == 1

        assert tasks[3].name == "Indented modern task"
        assert tasks[3].is_complete is True
        assert tasks[3].indentation_level == 1

        # Check complete tasks (both formats)
        assert tasks[4].name == "Complete traditional task"
        assert tasks[4].is_complete is True
        assert tasks[4].indentation_level == 0

        assert tasks[5].name == "Complete modern task"
        assert tasks[5].is_complete is True
        assert tasks[5].indentation_level == 0

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

    def test_content_without_dashes(self) -> None:
        """Test generating content using [ ] format without dashes."""
        tasks = [("Task without dash", False), ("Complete task", True)]

        content = create_test_tracker_content(tasks, use_dashes=False)

        assert "[ ] Task without dash" in content
        assert "[x] Complete task" in content
        # Should not contain dash format
        assert "- [ ]" not in content
        assert "- [x]" not in content

    def test_content_mixed_formats_helper(self) -> None:
        """Test that helper function can generate both formats."""
        tasks = [("Test task", False)]

        # Test with dashes (default)
        content_with_dashes = create_test_tracker_content(tasks, use_dashes=True)
        assert "- [ ] Test task" in content_with_dashes

        # Test without dashes
        content_without_dashes = create_test_tracker_content(tasks, use_dashes=False)
        assert "[ ] Test task" in content_without_dashes
        assert "- [ ]" not in content_without_dashes


class TestGetIncompleteTasksInternal:
    """Test _get_incomplete_tasks internal function."""

    def test_get_incomplete_basic(self) -> None:
        """Test getting incomplete tasks from content string."""
        content = """# Task Status Tracker

## Tasks

- [ ] Setup database
- [x] Add tests
- [ ] Write docs
"""
        result = _get_incomplete_tasks(content)
        assert result == ["Setup database", "Write docs"]

    def test_get_incomplete_with_meta_tasks_included(self) -> None:
        """Test getting incomplete tasks including meta-tasks."""
        content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
- [x] Create directories
- [ ] Add __init__.py files
- [ ] Prepare git commit message for step 1
- [ ] All Step 1 tasks completed
"""
        result = _get_incomplete_tasks(content, exclude_meta_tasks=False)
        expected = [
            "Add __init__.py files",
            "Prepare git commit message for step 1",
            "All Step 1 tasks completed",
        ]
        assert result == expected

    def test_get_incomplete_with_meta_tasks_excluded(self) -> None:
        """Test getting incomplete tasks excluding meta-tasks."""
        content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
- [x] Create directories
- [ ] Add __init__.py files
- [ ] Prepare git commit message for step 1
- [ ] All Step 1 tasks completed
"""
        result = _get_incomplete_tasks(content, exclude_meta_tasks=True)
        assert result == ["Add __init__.py files"]

    def test_get_incomplete_real_task_tracker_structure(self) -> None:
        """Test with real TASK_TRACKER.md structure."""
        content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
**File:** [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Create directory structure for llm package with subdirectories
- [x] Create all __init__.py files with appropriate docstrings
- [x] Verify all packages are importable
- [x] Run quality checks: pylint, pytest, mypy
- [x] Fix all issues found by quality checks
- [ ] Prepare git commit message for step 1
- [ ] All Step 1 tasks completed

### Step 2: Move Core Modules
**File:** [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Move llm_types.py → llm/types.py (preserve git history)
- [ ] Move llm_interface.py → llm/interface.py
- [ ] Move llm_serialization.py → llm/serialization.py
"""
        # Without filtering - gets meta-tasks from Step 1 first
        result_with_meta = _get_incomplete_tasks(content, exclude_meta_tasks=False)
        assert result_with_meta[0] == "Prepare git commit message for step 1"
        assert result_with_meta[1] == "All Step 1 tasks completed"
        assert len(result_with_meta) == 5  # 2 meta + 3 real from Step 2

        # With filtering - skips meta-tasks, goes straight to Step 2
        result_without_meta = _get_incomplete_tasks(content, exclude_meta_tasks=True)
        assert (
            result_without_meta[0]
            == "Move llm_types.py → llm/types.py (preserve git history)"
        )
        assert len(result_without_meta) == 3  # Only real tasks from Step 2

    def test_get_incomplete_all_complete(self) -> None:
        """Test when all tasks are complete."""
        content = """# Task Status Tracker

## Tasks

- [x] Task 1
- [x] Task 2
"""
        result = _get_incomplete_tasks(content)
        assert result == []

    def test_get_incomplete_section_not_found(self) -> None:
        """Test error when Implementation Steps section missing."""
        content = """# Task Status Tracker

## Some Other Section

- [ ] Not in implementation section
"""
        with pytest.raises(TaskTrackerSectionNotFoundError):
            _get_incomplete_tasks(content)


class TestGetIncompleteTasks:
    """Test get_incomplete_tasks function."""

    def test_get_incomplete_tasks_basic(self) -> None:
        """Test getting incomplete tasks from valid tracker file."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] Setup Data Models
- [x] Implement Parser  
- [ ] Add Tests
  - [ ] Unit tests
  - [x] Integration tests
- [x] Documentation
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            result = get_incomplete_tasks(temp_dir)

            # Should return only incomplete tasks
            expected = ["Setup Data Models", "Add Tests", "Unit tests"]
            assert result == expected

    def test_get_incomplete_tasks_without_dashes(self) -> None:
        """Test getting incomplete tasks from tracker file using [ ] format without dashes."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file using format without dashes (like current TASK_TRACKER.md)
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

[ ] Implement unit tests for validation
[x] Setup project structure
[ ] Create main classes
  [ ] Add helper methods
  [x] Implement core logic
[x] Add documentation
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            result = get_incomplete_tasks(temp_dir)

            # Should return only incomplete tasks from [ ] format
            expected = [
                "Implement unit tests for validation",
                "Create main classes",
                "Add helper methods",
            ]
            assert result == expected

    def test_get_incomplete_tasks_mixed_formats(self) -> None:
        """Test getting incomplete tasks from tracker file with mixed dash and no-dash formats."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file with both formats mixed
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] Traditional dash format task
[ ] Modern no-dash format task
- [x] Complete traditional task
[x] Complete modern task
  - [ ] Indented traditional subtask
  [ ] Indented modern subtask
  - [x] Complete indented traditional
  [x] Complete indented modern
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            result = get_incomplete_tasks(temp_dir)

            # Should return incomplete tasks from both formats
            expected = [
                "Traditional dash format task",
                "Modern no-dash format task",
                "Indented traditional subtask",
                "Indented modern subtask",
            ]
            assert result == expected

    def test_get_incomplete_tasks_empty_file(self) -> None:
        """Test behavior with missing tracker file."""
        with TemporaryDirectory() as temp_dir:
            # Test with missing file
            with pytest.raises(TaskTrackerFileNotFoundError):
                get_incomplete_tasks(temp_dir)

    def test_get_incomplete_tasks_no_incomplete(self) -> None:
        """Test when all tasks are complete."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker with all complete tasks
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [x] Setup Data Models
- [x] Implement Parser  
- [x] Add Tests
  - [x] Unit tests
  - [x] Integration tests
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            result = get_incomplete_tasks(temp_dir)

            # Should return empty list
            assert result == []

    def test_get_incomplete_tasks_no_section(self) -> None:
        """Test behavior when Implementation Steps section is missing."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker without Implementation Steps section
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Some Other Section

- [ ] Not an implementation task
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            with pytest.raises(TaskTrackerSectionNotFoundError):
                get_incomplete_tasks(temp_dir)

    def test_get_incomplete_tasks_default_folder(self) -> None:
        """Test get_incomplete_tasks with default folder path."""
        # Create pr_info directory in current working dir for test
        original_cwd = Path.cwd()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pr_info_path = temp_path / "pr_info"
            pr_info_path.mkdir()

            # Create test tracker file
            tracker_path = pr_info_path / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] Task 1
- [x] Task 2
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Change to temp directory and test default parameter
            import os

            os.chdir(temp_path)

            try:
                result = get_incomplete_tasks()  # Using default "pr_info"
                assert result == ["Task 1"]
            finally:
                # Restore original directory
                os.chdir(original_cwd)

    def test_get_incomplete_tasks_complex_names(self) -> None:
        """Test with complex task names including markdown formatting."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] **Step 1: Setup Data Models** - [step_1.md](steps/step_1.md)
  - [x] Create TaskInfo dataclass
  - [ ] Implement *exception hierarchy*
- [x] **Step 2: Core Parser** with [link](file.md)
- [ ] Step 3: [Another Link](path.md) and **formatting**
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            result = get_incomplete_tasks(temp_dir)

            # Names should be cleaned of markdown formatting
            expected = [
                "Step 1: Setup Data Models",
                "Implement exception hierarchy",
                "Step 3: Another Link and formatting",
            ]
            assert result == expected


class TestHasIncompleteWork:
    """Test has_incomplete_work function."""

    def test_has_work_with_incomplete_tasks(self) -> None:
        """Test returns True when there are incomplete tasks."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Tasks

- [x] Completed task
- [ ] Incomplete task
"""
            tracker_path.write_text(content, encoding="utf-8")

            result = has_incomplete_work(temp_dir)
            assert result is True

    def test_has_work_all_complete(self) -> None:
        """Test returns False when all tasks are complete."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Tasks

- [x] Task 1
- [x] Task 2
- [x] Task 3
"""
            tracker_path.write_text(content, encoding="utf-8")

            result = has_incomplete_work(temp_dir)
            assert result is False

    def test_has_work_empty_tracker(self) -> None:
        """Test returns False when there are no tasks."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Tasks

"""
            tracker_path.write_text(content, encoding="utf-8")

            result = has_incomplete_work(temp_dir)
            assert result is False


class TestGetStepProgress:
    """Test get_step_progress function with 2-tier hierarchy."""

    def test_single_step_progress(self) -> None:
        """Test progress for a single step with tasks."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
- [x] Create directory structure
- [x] Create __init__.py files
- [ ] Prepare git commit
- [ ] All tasks completed
"""
            tracker_path.write_text(content, encoding="utf-8")

            progress = get_step_progress(temp_dir)

            # Debug: print what we got
            print(f"Progress keys: {list(progress.keys())}")
            assert "Step 1: Create Package Structure" in progress
            step_info = progress["Step 1: Create Package Structure"]
            assert step_info["total"] == 4
            assert step_info["completed"] == 2
            assert step_info["incomplete"] == 2
            assert step_info["incomplete_tasks"] == [
                "Prepare git commit",
                "All tasks completed",
            ]

    def test_multiple_steps_progress(self) -> None:
        """Test progress for multiple steps."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
- [x] Create directory structure
- [x] Create __init__.py files

### Step 2: Move Core Modules
- [ ] Move llm_types.py
- [ ] Move llm_interface.py
- [ ] Move llm_serialization.py

### Step 3: Documentation
- [x] Update README
"""
            tracker_path.write_text(content, encoding="utf-8")

            progress = get_step_progress(temp_dir)

            # Check Step 1
            assert "Step 1: Create Package Structure" in progress
            step1 = progress["Step 1: Create Package Structure"]
            assert step1["total"] == 2
            assert step1["completed"] == 2
            assert step1["incomplete"] == 0
            assert step1["incomplete_tasks"] == []

            # Check Step 2
            assert "Step 2: Move Core Modules" in progress
            step2 = progress["Step 2: Move Core Modules"]
            assert step2["total"] == 3
            assert step2["completed"] == 0
            assert step2["incomplete"] == 3
            incomplete_tasks = step2["incomplete_tasks"]
            assert isinstance(incomplete_tasks, list)
            assert len(incomplete_tasks) == 3

            # Check Step 3
            assert "Step 3: Documentation" in progress
            step3 = progress["Step 3: Documentation"]
            assert step3["total"] == 1
            assert step3["completed"] == 1
            assert step3["incomplete"] == 0

    def test_step_with_nested_tasks(self) -> None:
        """Test step progress with indented sub-tasks."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

### Step 1: Setup
- [x] Task A
  - [x] Subtask A1
  - [ ] Subtask A2
- [ ] Task B
  - [ ] Subtask B1
"""
            tracker_path.write_text(content, encoding="utf-8")

            progress = get_step_progress(temp_dir)

            step1 = progress["Step 1: Setup"]
            # Should count all indented tasks under the step
            assert step1["total"] == 5  # Task A, A1, A2, Task B, B1
            assert step1["completed"] == 2  # Task A, A1
            assert step1["incomplete"] == 3  # A2, B, B1

    def test_current_task_tracker_structure_with_progress(self) -> None:
        """Test get_step_progress with real TASK_TRACKER.md structure."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
**File:** [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Create directory structure for llm package with subdirectories
- [x] Create all __init__.py files with appropriate docstrings
- [x] Verify all packages are importable
- [ ] Prepare git commit message for step 1
- [ ] All Step 1 tasks completed

### Step 2: Move Core Modules
**File:** [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Move llm_types.py → llm/types.py (preserve git history)
- [ ] Move llm_interface.py → llm/interface.py
"""
            tracker_path.write_text(content, encoding="utf-8")

            progress = get_step_progress(temp_dir)

            # Step 1 should show 3/5 complete
            step1 = progress["Step 1: Create Package Structure"]
            assert step1["total"] == 5
            assert step1["completed"] == 3
            assert step1["incomplete"] == 2

            # Step 2 should show 0/2 complete
            step2 = progress["Step 2: Move Core Modules"]
            assert step2["total"] == 2
            assert step2["completed"] == 0
            assert step2["incomplete"] == 2

            # has_incomplete_work should return True
            assert has_incomplete_work(temp_dir) is True


class TestGetIncompleteTasksEdgeCases:
    """Test edge cases and real-world scenarios for get_incomplete_tasks."""

    def test_current_task_tracker_structure(self) -> None:
        """Test with the actual current TASK_TRACKER.md structure to verify behavior.

        This test documents the current behavior with the real TASK_TRACKER.md structure
        that includes meta-tasks like 'Prepare git commit' and 'All Step X tasks completed'.
        """
        with TemporaryDirectory() as temp_dir:
            # Exact structure from current TASK_TRACKER.md (partial)
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
**File:** [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Create directory structure for llm package with subdirectories
- [x] Create all __init__.py files with appropriate docstrings
- [ ] Prepare git commit message for step 1
- [ ] All Step 1 tasks completed
"""
            tracker_path.write_text(content, encoding="utf-8")

            result = get_incomplete_tasks(temp_dir)

            # Document current behavior: includes meta-tasks
            assert len(result) == 2
            assert "Prepare git commit message for step 1" in result
            assert "All Step 1 tasks completed" in result


class TestIsTaskDone:
    """Test is_task_done function."""

    def test_is_task_done_complete_task(self) -> None:
        """Test checking completion status of completed task."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] Setup Data Models
- [x] Implement Parser  
- [ ] Add Tests
  - [x] Unit tests
  - [ ] Integration tests
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test with exact task name
            assert is_task_done("Implement Parser", temp_dir) is True
            assert is_task_done("Unit tests", temp_dir) is True

    def test_is_task_done_without_dashes(self) -> None:
        """Test checking completion status in files using [ ] format without dashes."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file using format without dashes
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

[ ] Setup Data Models
[x] Implement Parser
[ ] Add Tests
  [x] Unit tests
  [ ] Integration tests
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test with tasks in no-dash format
            assert is_task_done("Implement Parser", temp_dir) is True
            assert is_task_done("Unit tests", temp_dir) is True
            assert is_task_done("Setup Data Models", temp_dir) is False
            assert is_task_done("Add Tests", temp_dir) is False
            assert is_task_done("Integration tests", temp_dir) is False

    def test_is_task_done_mixed_formats(self) -> None:
        """Test checking completion status in files with mixed dash and no-dash formats."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file with both formats
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] Traditional incomplete task
[ ] Modern incomplete task
- [x] Traditional complete task
[x] Modern complete task
  - [ ] Traditional subtask incomplete
  [ ] Modern subtask incomplete
  - [x] Traditional subtask complete
  [x] Modern subtask complete
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test completion status for both formats
            assert is_task_done("Traditional incomplete task", temp_dir) is False
            assert is_task_done("Modern incomplete task", temp_dir) is False
            assert is_task_done("Traditional complete task", temp_dir) is True
            assert is_task_done("Modern complete task", temp_dir) is True
            assert is_task_done("Traditional subtask incomplete", temp_dir) is False
            assert is_task_done("Modern subtask incomplete", temp_dir) is False
            assert is_task_done("Traditional subtask complete", temp_dir) is True
            assert is_task_done("Modern subtask complete", temp_dir) is True

    def test_is_task_done_incomplete_task(self) -> None:
        """Test checking completion status of incomplete task."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [ ] Setup Data Models
- [x] Implement Parser  
- [ ] Add Tests
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test with incomplete task
            assert is_task_done("Setup Data Models", temp_dir) is False
            assert is_task_done("Add Tests", temp_dir) is False

    def test_is_task_done_case_insensitive_matching(self) -> None:
        """Test case-insensitive exact task name matching."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [x] Setup Data Models
- [ ] Implement Parser
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test case variations
            assert is_task_done("setup data models", temp_dir) is True
            assert is_task_done("SETUP DATA MODELS", temp_dir) is True
            assert is_task_done("Setup Data Models", temp_dir) is True
            assert is_task_done("implement parser", temp_dir) is False
            assert is_task_done("IMPLEMENT PARSER", temp_dir) is False

    def test_is_task_done_nonexistent_task(self) -> None:
        """Test behavior when task doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [x] Setup Data Models
- [ ] Implement Parser
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test with non-existent tasks
            assert is_task_done("Nonexistent Task", temp_dir) is False
            assert is_task_done("", temp_dir) is False
            assert is_task_done("Some Random Task", temp_dir) is False

    def test_is_task_done_with_markdown_formatting(self) -> None:
        """Test task matching with markdown formatting in file."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [x] **Step 1: Setup Data Models** - [step_1.md](steps/step_1.md)
- [ ] *Implement Core Parser*
- [x] Step 2: [Documentation](docs.md) and **formatting**
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test matching cleaned names
            assert is_task_done("Step 1: Setup Data Models", temp_dir) is True
            assert is_task_done("Implement Core Parser", temp_dir) is False
            assert (
                is_task_done("Step 2: Documentation and formatting", temp_dir) is True
            )

    def test_is_task_done_default_folder(self) -> None:
        """Test is_task_done with default folder path."""
        original_cwd = Path.cwd()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pr_info_path = temp_path / "pr_info"
            pr_info_path.mkdir()

            # Create test tracker file
            tracker_path = pr_info_path / "TASK_TRACKER.md"
            content = """# Task Status Tracker

### Implementation Steps

- [x] Task 1
- [ ] Task 2
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Change to temp directory and test default parameter
            import os

            os.chdir(temp_path)

            try:
                assert is_task_done("Task 1") is True  # Using default "pr_info"
                assert is_task_done("Task 2") is False
            finally:
                os.chdir(original_cwd)

    def test_is_task_done_missing_file(self) -> None:
        """Test behavior with missing tracker file."""
        with TemporaryDirectory() as temp_dir:
            # Test with missing file
            with pytest.raises(TaskTrackerFileNotFoundError):
                is_task_done("Any Task", temp_dir)

    def test_is_task_done_missing_section(self) -> None:
        """Test behavior when Implementation Steps section is missing."""
        with TemporaryDirectory() as temp_dir:
            # Create test tracker without Implementation Steps section
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Some Other Section

- [x] Not an implementation task
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test function
            with pytest.raises(TaskTrackerSectionNotFoundError):
                is_task_done("Any Task", temp_dir)


class TestNormalizeTaskName:
    """Test _normalize_task_name helper function."""

    def test_normalize_basic_strings(self) -> None:
        """Test basic string normalization."""
        assert _normalize_task_name("Setup Data Models") == "setup data models"
        assert _normalize_task_name("IMPLEMENT PARSER") == "implement parser"
        assert _normalize_task_name("Add Tests") == "add tests"

    def test_normalize_whitespace(self) -> None:
        """Test whitespace normalization."""
        assert _normalize_task_name("  Setup   Data   Models  ") == "setup data models"
        assert _normalize_task_name("\tTabbed\tTask\t") == "tabbed task"
        assert _normalize_task_name("\n\nNewline Task\n\n") == "newline task"

    def test_normalize_mixed_case_whitespace(self) -> None:
        """Test mixed case and whitespace normalization."""
        assert _normalize_task_name("  Setup   DATA   Models  ") == "setup data models"
        assert _normalize_task_name("IMPLEMENT    parser") == "implement parser"
        assert _normalize_task_name("Add\tTESTS   ") == "add tests"

    def test_normalize_empty_strings(self) -> None:
        """Test normalization of empty or whitespace-only strings."""
        assert _normalize_task_name("") == ""
        assert _normalize_task_name("   ") == ""
        assert _normalize_task_name("\t\n") == ""

    def test_parse_line_numbers_with_empty_lines(self) -> None:
        """Test that line numbers correctly match file lines including empty lines."""
        section_content = """- [ ] Task on line 1

- [x] Task on line 3


- [ ] Task on line 6"""
        tasks = _parse_task_lines(section_content)

        assert len(tasks) == 3

        # Verify line numbers match actual positions including empty lines
        assert tasks[0].name == "Task on line 1"
        assert tasks[0].line_number == 1

        assert tasks[1].name == "Task on line 3"
        assert tasks[1].line_number == 3

        assert tasks[2].name == "Task on line 6"
        assert tasks[2].line_number == 6

    def test_get_incomplete_tasks_with_meta_tasks_excluded(self) -> None:
        """Test getting incomplete tasks with meta-tasks excluded.

        This test verifies the fix for the issue where the workflow was getting
        meta-tasks like 'Prepare git commit message' as the next task to implement.

        With exclude_meta_tasks=True, it should skip meta-tasks and return only
        real implementation tasks.
        """
        with TemporaryDirectory() as temp_dir:
            # Create test tracker file matching current TASK_TRACKER.md structure
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

### Step 1: Create Package Structure
**File:** [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Create directory structure for llm package with subdirectories
- [x] Create all __init__.py files with appropriate docstrings
- [x] Verify all packages are importable
- [x] Run quality checks: pylint, pytest, mypy
- [x] Fix all issues found by quality checks
- [ ] Prepare git commit message for step 1
- [ ] All Step 1 tasks completed

### Step 2: Move Core Modules
**File:** [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Move llm_types.py → llm/types.py (preserve git history)
- [ ] Move llm_interface.py → llm/interface.py
- [ ] Move llm_serialization.py → llm/serialization.py
- [ ] Update llm/__init__.py with public API exports

### Pull Request

- [ ] Review all changes and ensure consistency
- [ ] Submit pull request for review
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Test WITHOUT filtering (old behavior)
            result_with_meta = get_incomplete_tasks(temp_dir, exclude_meta_tasks=False)
            # Should include meta-tasks
            assert "Prepare git commit message for step 1" in result_with_meta
            assert "All Step 1 tasks completed" in result_with_meta
            assert len(result_with_meta) == 6  # 2 meta from Step 1 + 4 from Step 2

            # Test WITH filtering (new behavior)
            result_without_meta = get_incomplete_tasks(
                temp_dir, exclude_meta_tasks=True
            )
            # Should skip meta-tasks and go straight to Step 2 implementation tasks
            expected = [
                "Move llm_types.py → llm/types.py (preserve git history)",
                "Move llm_interface.py → llm/interface.py",
                "Move llm_serialization.py → llm/serialization.py",
                "Update llm/__init__.py with public API exports",
            ]
            assert result_without_meta == expected
