from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    get_step_progress,
    get_task_counts,
    has_incomplete_work,
    is_task_done,
)
from tests.workflow_utils.test_task_tracker import create_test_tracker_content


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


class TestGetTaskCounts:
    """Tests for the get_task_counts() function."""

    def test_get_task_counts_all_complete(self) -> None:
        """Tracker with all [x] returns (N, N)."""
        content = create_test_tracker_content(
            [("Task A", True), ("Task B", True), ("Task C", True)]
        )
        with TemporaryDirectory() as tmpdir:
            Path(tmpdir, "TASK_TRACKER.md").write_text(content, encoding="utf-8")
            total, completed = get_task_counts(tmpdir)
            assert total == 3
            assert completed == 3

    def test_get_task_counts_some_incomplete(self) -> None:
        """Mixed tasks return (total, completed) where completed < total."""
        content = create_test_tracker_content(
            [("Task A", True), ("Task B", False), ("Task C", True), ("Task D", False)]
        )
        with TemporaryDirectory() as tmpdir:
            Path(tmpdir, "TASK_TRACKER.md").write_text(content, encoding="utf-8")
            total, completed = get_task_counts(tmpdir)
            assert total == 4
            assert completed == 2

    def test_get_task_counts_empty_section(self) -> None:
        """Tasks section with no checkboxes returns (0, 0)."""
        content = "# Tracker\n\n## Tasks\n\nNo tasks here.\n\n## Pull Request\n"
        with TemporaryDirectory() as tmpdir:
            Path(tmpdir, "TASK_TRACKER.md").write_text(content, encoding="utf-8")
            total, completed = get_task_counts(tmpdir)
            assert total == 0
            assert completed == 0

    def test_get_task_counts_file_not_found(self) -> None:
        """Raises TaskTrackerFileNotFoundError when file missing."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(TaskTrackerFileNotFoundError):
                get_task_counts(tmpdir)

    def test_get_task_counts_section_not_found(self) -> None:
        """Raises TaskTrackerSectionNotFoundError when Tasks section missing."""
        content = "# Tracker\n\n## Some Other Section\n\nNo tasks section.\n"
        with TemporaryDirectory() as tmpdir:
            Path(tmpdir, "TASK_TRACKER.md").write_text(content, encoding="utf-8")
            with pytest.raises(TaskTrackerSectionNotFoundError):
                get_task_counts(tmpdir)
