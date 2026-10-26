from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerSectionNotFoundError,
    _find_implementation_section,
    _normalize_task_name,
    _parse_task_lines,
    get_incomplete_tasks,
)
from tests.workflow_utils.test_task_tracker import create_test_tracker_content


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

    def test_empty_tasks_section(self) -> None:
        """Test that empty Tasks section returns empty string."""
        content = """# Task Tracker

## Tasks
## Pull Request
- [ ] Create PR
"""
        section = _find_implementation_section(content)
        assert section.strip() == ""


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
