from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TASK_TRACKER_TEMPLATE,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    validate_task_tracker,
)


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
