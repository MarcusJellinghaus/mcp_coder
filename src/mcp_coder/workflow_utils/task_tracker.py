"""Task tracker parsing functionality for TASK_TRACKER.md files.

This module provides utilities to parse markdown task tracker files with GitHub-style
checkboxes and extract incomplete implementation tasks for automated workflow management.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

# Compiled regex patterns for better performance
# Updated to handle both "- [ ]" and "[ ]" formats
CHECKBOX_PATTERN = re.compile(r"^(-\s*)?\[([\s]|[xX])\]")
BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_PATTERN = re.compile(r"\*([^*]+)\*")
LINK_REFERENCE_PATTERN = re.compile(r"\s*-\s*\[[^\]]+\]\([^\)]+\)\s*$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
CHECKBOX_REMOVE_PATTERN = re.compile(r"^\s*(-\s*)?\[[\s\w]\]\s*")
WHITESPACE_PATTERN = re.compile(r"\s+")


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
    """Find and extract Implementation Steps or Tasks section, raise exception if missing.

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        Content of Implementation Steps or Tasks section (without header)

    Raises:
        TaskTrackerSectionNotFoundError: If Implementation Steps or Tasks section not found
    """
    lines = content.split("\n")
    in_impl_section = False
    impl_section_level = 0  # Track the header level of the implementation section
    impl_lines = []

    for line in lines:
        # Check for section headers (## or ###)
        if line.strip().startswith(("##", "###")):
            # Count the number of # characters to determine header level
            header_level = len(line.strip()) - len(line.strip().lstrip("#"))
            header_text = line.strip().lstrip("#").strip().lower()

            # Look for either "implementation steps" or "tasks" sections
            if "implementation steps" in header_text or header_text == "tasks":
                in_impl_section = True
                impl_section_level = header_level
                continue
            elif in_impl_section:
                # Stop parsing when we hit Pull Request section
                if "pull request" in header_text:
                    break
                # Stop parsing if we hit a same-level or higher-level section
                # (lower numbers mean higher level: ## is level 2, ### is level 3)
                elif header_level <= impl_section_level:
                    break
                # Otherwise, this is a subsection within our implementation section
                # Continue collecting it

        # Collect lines if we're in the implementation section
        if in_impl_section:
            impl_lines.append(line)

    if not in_impl_section:
        raise TaskTrackerSectionNotFoundError(
            "Implementation Steps or Tasks section not found in TASK_TRACKER.md"
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

    # Match task lines: "- [ ]" or "- [x]" or "[ ]" or "[x]" or "[X]"
    match = CHECKBOX_PATTERN.match(stripped)
    if not match:
        return False, False

    checkbox_content = (
        match.group(2).strip().lower()
    )  # Changed from group(1) to group(2)
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
    cleaned = CHECKBOX_REMOVE_PATTERN.sub("", raw_line)

    # Remove markdown bold/italic formatting
    cleaned = BOLD_PATTERN.sub(r"\1", cleaned)  # **bold**
    cleaned = ITALIC_PATTERN.sub(r"\1", cleaned)  # *italic*

    # Remove link references like "- [file.md](path)" at the end
    cleaned = LINK_REFERENCE_PATTERN.sub("", cleaned)

    # Remove markdown links: [text](url)
    cleaned = MARKDOWN_LINK_PATTERN.sub(r"\1", cleaned)

    # Clean up multiple spaces and strip
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned).strip()

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

    for line_number, line in enumerate(lines, start=1):
        is_task, is_complete = _is_task_line(line)

        if is_task:
            # Calculate indentation level (count spaces before checkbox)
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

    return tasks


def _normalize_task_name(name: str) -> str:
    """Normalize task name for case-insensitive exact matching.

    Args:
        name: Task name to normalize

    Returns:
        Normalized task name (lowercase, normalized whitespace)
    """
    return WHITESPACE_PATTERN.sub(" ", name.strip().lower())


def get_incomplete_tasks(folder_path: str = "pr_info") -> list[str]:
    """Get list of incomplete task names from Implementation Steps section.

    Args:
        folder_path: Path to folder containing TASK_TRACKER.md (default: "pr_info")

    Returns:
        List of incomplete task names

    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md not found
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found

    Examples:
        >>> get_incomplete_tasks("my_project")
        ["Setup database", "Add authentication", "Write documentation"]

        >>> get_incomplete_tasks()  # Uses default "pr_info" folder
        ["Implement API endpoints", "Add unit tests"]

        >>> get_incomplete_tasks("empty_project")
        []  # No incomplete tasks found
    """
    # Read the tracker file
    content = _read_task_tracker(folder_path)

    # Find the Implementation Steps section
    section_content = _find_implementation_section(content)

    # Parse all tasks
    all_tasks = _parse_task_lines(section_content)

    # Filter for incomplete tasks and return their names
    incomplete_tasks = [task.name for task in all_tasks if not task.is_complete]

    return incomplete_tasks


def has_incomplete_work(folder_path: str = "pr_info") -> bool:
    """Check if there is any incomplete work in the task tracker.

    This is a simple yes/no check across all steps and tasks.

    Args:
        folder_path: Path to folder containing TASK_TRACKER.md (default: "pr_info")

    Returns:
        True if there are any incomplete tasks, False otherwise

    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md not found
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found

    Examples:
        >>> has_incomplete_work("my_project")
        True  # There are incomplete tasks

        >>> has_incomplete_work("completed_project")
        False  # All tasks are complete
    """
    incomplete_tasks = get_incomplete_tasks(folder_path)
    return len(incomplete_tasks) > 0


def get_step_progress(
    folder_path: str = "pr_info",
) -> dict[str, dict[str, int | list[str]]]:
    """Get detailed progress information for each step.

    Returns a 2-tier hierarchy: steps (markdown headers) containing tasks (checkboxes).

    Args:
        folder_path: Path to folder containing TASK_TRACKER.md (default: "pr_info")

    Returns:
        Dictionary mapping step names to their progress info:
        {
            "Step 1: Create Package Structure": {
                "total": 5,
                "completed": 3,
                "incomplete": 2,
                "incomplete_tasks": ["Task A", "Task B"]
            },
            ...
        }

    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md not found
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found

    Examples:
        >>> progress = get_step_progress("my_project")
        >>> for step, info in progress.items():
        ...     print(f"{step}: {info['completed']}/{info['total']} complete")
        Step 1: Create Package Structure: 3/5 complete
        Step 2: Move Core Modules: 0/4 complete
    """
    # Read the tracker file
    content = _read_task_tracker(folder_path)

    # Find the Implementation Steps section
    section_content = _find_implementation_section(content)

    # Parse tasks and track step headers from markdown
    lines = section_content.split("\n")
    progress: dict[str, dict[str, int | list[str]]] = {}
    current_step_name: str | None = None
    current_step_tasks: list[TaskInfo] = []

    # Also parse all tasks to get TaskInfo objects
    all_tasks = _parse_task_lines(section_content)
    task_index = 0

    for line in lines:
        # Check if this is a step header (### Step N:)
        if line.strip().startswith("###"):
            # Save previous step if exists
            if current_step_name and current_step_tasks:
                _save_step_progress(progress, current_step_name, current_step_tasks)

            # Extract step name from header
            current_step_name = line.strip().lstrip("#").strip()
            current_step_tasks = []
        # Check if this line is a task checkbox
        elif line.strip() and CHECKBOX_PATTERN.match(line.strip()):
            # Add task to current step
            if current_step_name and task_index < len(all_tasks):
                current_step_tasks.append(all_tasks[task_index])
                task_index += 1

    # Save last step
    if current_step_name and current_step_tasks:
        _save_step_progress(progress, current_step_name, current_step_tasks)

    return progress


def _save_step_progress(
    progress: dict[str, dict[str, int | list[str]]],
    step_name: str,
    tasks: list[TaskInfo],
) -> None:
    """Helper to save step progress information."""
    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_complete)
    incomplete = total - completed
    incomplete_task_names = [t.name for t in tasks if not t.is_complete]

    progress[step_name] = {
        "total": total,
        "completed": completed,
        "incomplete": incomplete,
        "incomplete_tasks": incomplete_task_names,
    }


def is_task_done(task_name: str, folder_path: str = "pr_info") -> bool:
    """Check if specific task is marked as complete.

    Args:
        task_name: Name of task to check (case-insensitive exact match)
        folder_path: Path to folder containing TASK_TRACKER.md (default: "pr_info")

    Returns:
        True if task is complete ([x] or [X]), False if incomplete or not found

    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md not found
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found

    Examples:
        >>> is_task_done("Setup database", "my_project")
        True  # Task is marked as [x]

        >>> is_task_done("add authentication")  # Case-insensitive matching
        False  # Task is marked as [ ] or not found

        >>> is_task_done("Setup Database")  # Matches "setup database" in file
        True  # Case-insensitive exact matching

        >>> is_task_done("Nonexistent Task")
        False  # Task not found in tracker
    """
    # Read the tracker file
    content = _read_task_tracker(folder_path)

    # Find the Implementation Steps section
    section_content = _find_implementation_section(content)

    # Parse all tasks
    all_tasks = _parse_task_lines(section_content)

    # Normalize the input task name for comparison
    normalized_input = _normalize_task_name(task_name)

    # Find matching task using case-insensitive exact matching
    for task in all_tasks:
        normalized_task = _normalize_task_name(task.name)
        if normalized_task == normalized_input:
            return task.is_complete

    # Task not found - return False
    return False
