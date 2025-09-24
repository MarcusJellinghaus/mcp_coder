"""Task tracker parsing functionality for TASK_TRACKER.md files.

This module provides utilities to parse markdown task tracker files with GitHub-style
checkboxes and extract incomplete implementation tasks for automated workflow management.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TaskInfo:
    """Simple data model for task information.

    Attributes:
        name: Clean task name without markdown formatting
        is_complete: True if task is marked as complete ([x] or [X])
        line_number: Line number in the original file (1-based)
        indentation_level: Indentation depth (0 for top-level, 1 for first indent, etc.)
    """

    name: str
    is_complete: bool
    line_number: int
    indentation_level: int


class TaskTrackerError(Exception):
    """Base exception for task tracker issues."""

    pass


class TaskTrackerFileNotFoundError(TaskTrackerError):
    """TASK_TRACKER.md file not found."""

    pass


class TaskTrackerSectionNotFoundError(TaskTrackerError):
    """Implementation Steps section not found."""

    pass


def _read_task_tracker(folder_path: str) -> str:
    """Read TASK_TRACKER.md file content, raise exception if missing.

    Args:
        folder_path: Path to folder containing TASK_TRACKER.md

    Returns:
        Content of TASK_TRACKER.md file

    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md file doesn't exist
    """
    tracker_path = Path(folder_path) / "TASK_TRACKER.md"

    if not tracker_path.exists():
        raise TaskTrackerFileNotFoundError(
            f"TASK_TRACKER.md not found at {tracker_path}"
        )

    return tracker_path.read_text(encoding="utf-8")
