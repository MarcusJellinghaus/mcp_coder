"""Shared prerequisite steps for workflows.

Workflow-agnostic prerequisite kernels shared by multiple orchestrators. The
git-cleanliness determination lives here (the middle tier) so ``implement`` and
``create_pr`` share a single implementation instead of duplicating it.
"""

import logging
from pathlib import Path
from typing import Optional

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


def is_branch_not_base(
    current_branch: Optional[str], base_branch: Optional[str]
) -> bool:
    """Check that the current branch is a valid, non-base feature branch.

    Pure comparison step: it does not resolve either branch itself. Callers
    resolve ``current_branch`` and ``base_branch`` with their own git resolvers
    (e.g. the default branch for ``implement`` or a possibly-custom base for
    ``create_pr``) and pass the results here.

    Args:
        current_branch: Name of the current branch, or None if it could not be
            determined (e.g. detached HEAD).
        base_branch: Name of the base branch, or None if it could not be
            determined.

    Returns:
        True if ``current_branch`` is a valid branch that differs from
        ``base_branch``, False otherwise.

    Note:
        Never raises; logs an error describing the failing condition. Any
        exception from resolving the branches stays in the caller.
    """
    if current_branch is None:
        logger.error(
            "Could not determine current branch (possibly detached HEAD state)"
        )
        return False

    if base_branch is None:
        logger.error("Could not determine base branch")
        return False

    if current_branch == base_branch:
        logger.error(
            f"Current branch '{current_branch}' is the base branch. "
            "Please create and switch to a feature branch before running the workflow."
        )
        return False

    logger.info(
        f"Current branch '{current_branch}' is not the base branch '{base_branch}' - check passed"
    )
    return True
