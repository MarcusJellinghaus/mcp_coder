"""Task tracker parsing functionality for TASK_TRACKER.md files.

This module provides utilities to parse markdown task tracker files with GitHub-style
checkboxes and extract incomplete implementation tasks for automated workflow management.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


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


def _find_implementation_section(content: str) -> str:
    """Find and extract Implementation Steps section, raise exception if missing.

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        Content of Implementation Steps section (without header)

    Raises:
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found
    """
    lines = content.split("\n")
    in_impl_section = False
    impl_lines = []

    for line in lines:
        # Check for section headers (## or ###)
        if line.strip().startswith(("##", "###")):
            header_text = line.strip().lstrip("#").strip().lower()

            if "implementation steps" in header_text:
                in_impl_section = True
                continue
            elif "pull request" in header_text and in_impl_section:
                # Stop parsing when we hit Pull Request section
                break
            elif in_impl_section:
                # Hit another section while in impl section - stop parsing
                break

        # Collect lines if we're in the implementation section
        if in_impl_section:
            impl_lines.append(line)

    if not in_impl_section:
        raise TaskTrackerSectionNotFoundError(
            "Implementation Steps section not found in TASK_TRACKER.md"
        )

    return "\n".join(impl_lines)


def _is_task_line(line: str) -> Tuple[bool, bool]:
    """Detect if line is a task and whether it's complete.

    Args:
        line: Line of text to check

    Returns:
        Tuple of (is_task_line, is_complete)
    """
    stripped = line.strip()

    # Match task lines: "- [ ]" or "- [x]" or "- [X]" only
    match = re.match(r"^-\s*\[([\s]|[xX])\]", stripped)
    if not match:
        return False, False

    checkbox_content = match.group(1).strip().lower()
    is_complete = checkbox_content == "x"

    return True, is_complete


def _clean_task_name(raw_line: str) -> str:
    """Clean task name by removing markdown formatting and extra whitespace.

    Args:
        raw_line: Raw line containing task checkbox and name

    Returns:
        Cleaned task name
    """
    # Remove checkbox pattern at start
    cleaned = re.sub(r"^\s*-\s*\[[\s\w]\]\s*", "", raw_line)

    # Remove markdown bold/italic formatting
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)  # **bold**
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)  # *italic*

    # Remove link references like "- [file.md](path)" at the end
    cleaned = re.sub(r"\s*-\s*\[[^\]]+\]\([^\)]+\)\s*$", "", cleaned)

    # Remove markdown links: [text](url)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)

    # Clean up multiple spaces and strip
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def _parse_task_lines(section_content: str) -> list[TaskInfo]:
    """Parse individual task lines and extract TaskInfo objects with indentation levels.

    Args:
        section_content: Content of Implementation Steps section

    Returns:
        List of TaskInfo objects with line numbers and indentation levels
    """
    if not section_content.strip():
        return []

    lines = section_content.split("\n")
    tasks = []
    line_number = 1

    for line in lines:
        is_task, is_complete = _is_task_line(line)

        if is_task:
            # Calculate indentation level (count spaces before '-')
            leading_spaces = len(line) - len(line.lstrip())
            # Assume 2 spaces per indentation level
            indentation_level = leading_spaces // 2

            # Clean the task name
            task_name = _clean_task_name(line)

            if task_name:  # Only add if we have a valid task name
                task_info = TaskInfo(
                    name=task_name,
                    is_complete=is_complete,
                    line_number=line_number,
                    indentation_level=indentation_level,
                )
                tasks.append(task_info)

        # Only count non-empty lines for line numbering
        if line.strip():
            line_number += 1

    return tasks
