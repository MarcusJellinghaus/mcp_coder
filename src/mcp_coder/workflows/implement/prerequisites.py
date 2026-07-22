"""Prerequisites validation for implement workflow.

This module handles git status, branch checking, and project validation
for the automated implementation workflow.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    get_current_branch_name,
    get_default_branch_name,
)
from mcp_coder.workflow_steps.prerequisites import check_git_clean, is_branch_not_base
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerSectionNotFoundError,
    _find_implementation_section,
    _parse_task_lines,
    _read_task_tracker,
    validate_task_tracker,
)

from .constants import PR_INFO_DIR

logger = logging.getLogger(__name__)

# Re-exported from the shared workflow_steps layer so existing callers and
# ``from .prerequisites import check_git_clean`` keep working unchanged.
__all__ = [
    "check_git_clean",
    "check_main_branch",
    "check_prerequisites",
    "has_implementation_tasks",
]


def check_main_branch(project_dir: Path) -> bool:
    """Check if current branch is not the main branch.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if current branch is not main, False otherwise

    Note:
        Validates both current and default branch names exist.
        Handles exceptions from git operations gracefully.
    """
    logger.info("Checking current branch...")

    try:
        current_branch = get_current_branch_name(project_dir)
        main_branch = get_default_branch_name(project_dir)
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error checking current branch: {e}")
        return False

    return is_branch_not_base(current_branch, main_branch)


def check_prerequisites(project_dir: Path) -> bool:
    """Verify dependencies and prerequisites are met.

    Now also handles TASK_TRACKER.md lifecycle:
    - Fails if pr_info/ folder is missing (must run create_plan first)
    - Validates structure of existing TASK_TRACKER.md

    Args:
        project_dir: Path to the project directory

    Returns:
        True if all prerequisites are met, False otherwise

    Note:
        Checks for git repository and task tracker file existence.
        Does not perform git operations, only file system checks.
    """
    logger.info("Checking prerequisites...")

    # Check if we're in a git repository
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        logger.error(f"Not a git repository: {project_dir}")
        return False

    # Check pr_info directory exists (created by create_plan workflow)
    pr_info_path = project_dir / PR_INFO_DIR
    if not pr_info_path.exists():
        logger.error("folder pr_info not found. Run 'create_plan' first.")
        return False

    # Check TASK_TRACKER.md exists
    task_tracker_path = pr_info_path / "TASK_TRACKER.md"
    if not task_tracker_path.exists():
        logger.error(f"{task_tracker_path} not found")
        return False

    # Validate existing structure
    try:
        validate_task_tracker(str(pr_info_path))
        logger.info("Task tracker structure validated")
    except TaskTrackerSectionNotFoundError as e:
        logger.error(f"Invalid task tracker structure: {e}")
        return False

    logger.info("Prerequisites check passed")
    return True


def has_implementation_tasks(project_dir: Path) -> bool:
    """Check if TASK_TRACKER.md has any implementation tasks (complete or incomplete).

    Args:
        project_dir: Path to the project directory

    Returns:
        True if implementation tasks exist, False otherwise

    Note:
        Uses internal task tracker functions to parse the file.
        Returns False if any exception occurs during parsing.
    """
    try:
        # Use internal functions to check for ANY tasks (complete or incomplete)
        pr_info_dir = str(project_dir / PR_INFO_DIR)
        content = _read_task_tracker(pr_info_dir)
        section_content = _find_implementation_section(content)
        all_tasks = _parse_task_lines(section_content)

        # Return True if there are any tasks at all (complete or incomplete)
        return len(all_tasks) > 0
    except (
        Exception
    ):  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        # If any exception occurs (file not found, section not found, etc.),
        # it means there are no proper implementation tasks
        return False
