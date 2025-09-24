"""Integration tests for task tracker functionality.

Simple tests to verify task tracker integrates properly with workflow_utils package.
"""

import tempfile
from pathlib import Path

import pytest

from mcp_coder.workflow_utils import (
    TaskTrackerFileNotFoundError,
    get_incomplete_tasks,
    is_task_done,
)


class TestTaskTrackerIntegration:
    """Integration tests for task tracker with workflow_utils package."""

    def test_imports_work(self):
        """Test importing task tracker functions from workflow_utils package."""
        from mcp_coder.workflow_utils import get_incomplete_tasks, is_task_done

        assert callable(get_incomplete_tasks)
        assert callable(is_task_done)

    def test_basic_functionality(self):
        """Test basic end-to-end functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tracker_file = temp_path / "TASK_TRACKER.md"

            tracker_content = """# Test Tracker

## Implementation Steps

- [x] Complete task
- [ ] Incomplete task
"""
            tracker_file.write_text(tracker_content, encoding="utf-8")

            # Test getting incomplete tasks
            incomplete = get_incomplete_tasks(str(temp_path))
            assert incomplete == ["Incomplete task"]

            # Test checking task status
            assert is_task_done("Complete task", str(temp_path))
            assert not is_task_done("Incomplete task", str(temp_path))

    def test_missing_file_raises_error(self):
        """Test error handling for missing tracker file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(TaskTrackerFileNotFoundError):
                get_incomplete_tasks(str(temp_dir))
