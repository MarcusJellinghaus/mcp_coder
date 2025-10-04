"""Prerequisites validation for implement workflow.

This module handles git status, branch checking, and project validation
for the automated implementation workflow.
"""

import logging
from pathlib import Path

from mcp_coder.utils.git_operations import (
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    is_working_directory_clean,
)
from mcp_coder.workflow_utils.task_tracker import (
    _find_implementation_section,
    _parse_task_lines,
    _read_task_tracker,
)

logger = logging.getLogger(__name__)

# Constants
PR_INFO_DIR = "pr_info"


def check_git_clean(project_dir: Path) -> bool:
    """Check if git working directory is clean.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if working directory is clean, False otherwise

    Note:
        Logs detailed status information when directory is dirty.
        Handles ValueError exceptions from git operations.
    """
    logger.info("Checking git working directory status...")

    try:
        is_clean = is_working_directory_clean(project_dir)

        if not is_clean:
            logger.error(
                "Git working directory is not clean. Please commit or stash changes before running the workflow."
            )
            # Get detailed status for error reporting
            try:
                status = get_full_status(project_dir)
                for category, files in status.items():
                    if files:
                        logger.error(f"{category.capitalize()} files: {files}")
            except Exception as e:
                logger.debug(f"Could not get detailed status: {e}")
            return False

        logger.info("Git working directory is clean")
        return True

    except ValueError as e:
        logger.error(str(e))
        return False


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

        if current_branch is None:
            logger.error(
                "Could not determine current branch (possibly detached HEAD state)"
            )
            return False

        if main_branch is None:
            logger.error(
                "Could not determine main branch (neither 'main' nor 'master' branch found)"
            )
            return False

        if current_branch == main_branch:
            logger.error(
                f"Current branch '{current_branch}' is the main branch. Please create and switch to a feature branch before running the workflow."
            )
            return False

        logger.info(
            f"Current branch '{current_branch}' is not the main branch '{main_branch}' - check passed"
        )
        return True

    except Exception as e:
        logger.error(f"Error checking current branch: {e}")
        return False


def check_prerequisites(project_dir: Path) -> bool:
    """Verify dependencies and prerequisites are met.

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

    # Check if task tracker exists
    task_tracker_path = project_dir / PR_INFO_DIR / "TASK_TRACKER.md"
    if not task_tracker_path.exists():
        logger.error(f"{task_tracker_path} not found")
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
    except Exception:
        # If any exception occurs (file not found, section not found, etc.),
        # it means there are no proper implementation tasks
        return False
