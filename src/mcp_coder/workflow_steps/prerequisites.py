"""Shared prerequisite steps for workflows.

Workflow-agnostic prerequisite kernels shared by multiple orchestrators. The
git-cleanliness determination lives here (the middle tier) so ``implement`` and
``create_pr`` share a single implementation instead of duplicating it.
"""

import logging
from pathlib import Path

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from mcp_coder.mcp_workspace_git import get_full_status, is_working_directory_clean

logger = logging.getLogger(__name__)


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
        is_clean = is_working_directory_clean(
            project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        )

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
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
                logger.debug(f"Could not get detailed status: {e}")
            return False

        logger.info("Git working directory is clean")
        return True

    except ValueError as e:
        logger.error(str(e))
        return False
