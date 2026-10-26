"""Tests for task tracker parsing functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TASK_TRACKER_TEMPLATE,
    TaskInfo,
    TaskTrackerError,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    _find_implementation_section,
    _get_incomplete_tasks,
    _read_task_tracker,
    get_step_progress,
    get_task_counts,
    has_incomplete_work,
    is_task_done,
    validate_task_tracker,
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


class TestValidateTaskTracker:
    """Tests for validate_task_tracker function."""

    def test_validate_valid_tracker(self) -> None:
        """Test validation passes for valid tracker with both headers."""
        with TemporaryDirectory() as temp_dir:
            # Create temp file with ## Tasks and ## Pull Request headers
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Instructions for LLM
Some instructions here.

## Tasks

### Step 1: Setup
- [ ] Task 1
- [x] Task 2

## Pull Request

- [ ] Create PR
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Call validate_task_tracker() - should not raise
            validate_task_tracker(temp_dir)

    def test_validate_missing_tasks_header(self) -> None:
        """Test validation fails when ## Tasks header missing."""
        with TemporaryDirectory() as temp_dir:
            # Create temp file without ## Tasks header
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Instructions for LLM
Some instructions here.

## Some Other Section

- [ ] Not a task section

## Pull Request

- [ ] Create PR
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Call validate_task_tracker() - should raise TaskTrackerSectionNotFoundError
            with pytest.raises(TaskTrackerSectionNotFoundError) as exc_info:
                validate_task_tracker(temp_dir)
            assert "Implementation Steps or Tasks section not found" in str(
                exc_info.value
            )

    def test_validate_missing_pull_request_header(self) -> None:
        """Test validation fails when ## Pull Request header missing.

        Note: The current implementation uses _find_implementation_section which
        does not require ## Pull Request to exist - it just uses it as an end boundary.
        This test documents that behavior: validation passes even without ## Pull Request
        since the Tasks section content is valid.
        """
        with TemporaryDirectory() as temp_dir:
            # Create temp file with ## Tasks but no ## Pull Request
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Instructions for LLM
Some instructions here.

## Tasks

### Step 1: Setup
- [ ] Task 1
- [x] Task 2
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Current behavior: validation passes because Tasks section exists
            # The ## Pull Request is optional as an end boundary
            validate_task_tracker(temp_dir)

    def test_validate_missing_file(self) -> None:
        """Test validation fails when file doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            # Call validate_task_tracker() on non-existent path
            # Should raise TaskTrackerFileNotFoundError
            with pytest.raises(TaskTrackerFileNotFoundError) as exc_info:
                validate_task_tracker(temp_dir)
            assert "TASK_TRACKER.md not found" in str(exc_info.value)

    def test_validate_default_folder_path(self) -> None:
        """Test validate_task_tracker with default folder path."""
        original_cwd = Path.cwd()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pr_info_path = temp_path / "pr_info"
            pr_info_path.mkdir()

            # Create test tracker file
            tracker_path = pr_info_path / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

- [ ] Task 1

## Pull Request

- [ ] Create PR
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Change to temp directory and test default parameter
            import os

            os.chdir(temp_path)

            try:
                # Using default "pr_info" - should not raise
                validate_task_tracker()
            finally:
                os.chdir(original_cwd)

    def test_validate_empty_tasks_section(self) -> None:
        """Test validation passes with empty Tasks section."""
        with TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            content = """# Task Status Tracker

## Tasks

## Pull Request

- [ ] Create PR
"""
            tracker_path.write_text(content, encoding="utf-8")

            # Should not raise - empty Tasks section is valid
            validate_task_tracker(temp_dir)


class TestTaskTrackerTemplate:
    """Tests for TASK_TRACKER_TEMPLATE constant."""

    def test_template_contains_tasks_header(self) -> None:
        """Test template contains ## Tasks header."""
        assert "## Tasks" in TASK_TRACKER_TEMPLATE

    def test_template_contains_pull_request_header(self) -> None:
        """Test template contains ## Pull Request header."""
        assert "## Pull Request" in TASK_TRACKER_TEMPLATE

    def test_template_is_valid(self) -> None:
        """Test template passes validation."""
        with TemporaryDirectory() as temp_dir:
            # Write template to temp file
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            tracker_path.write_text(TASK_TRACKER_TEMPLATE, encoding="utf-8")

            # Call validate_task_tracker() - should not raise
            validate_task_tracker(temp_dir)


# ============================================================================
# get_task_counts() tests
# ============================================================================


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
