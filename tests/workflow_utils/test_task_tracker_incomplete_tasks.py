from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    _get_incomplete_tasks,
    get_incomplete_tasks,
    has_incomplete_work,
)


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
