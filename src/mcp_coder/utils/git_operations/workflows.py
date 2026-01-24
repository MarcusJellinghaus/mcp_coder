"""Git workflow orchestration layer.

This module coordinates multiple git operations to accomplish complex workflows.
It serves as Layer 0 in the git operations architecture.

Constraints:
- Can only import from same module (git_operations.*)
- Cannot call external APIs (GitHub, Jenkins, etc.)
- Cannot import from other domains (github_operations, etc.)
- Coordinates multiple git operations for business workflows
"""

import logging
from pathlib import Path

from .commits import commit_staged_files
from .core import CommitResult
from .readers import get_full_status, is_git_repository
from .staging import stage_all_changes

# Use same logging pattern as other git_operations modules
logger = logging.getLogger(__name__)


def commit_all_changes(message: str, project_dir: Path) -> CommitResult:
    """
    Orchestrate workflow: stage all unstaged changes and commit them in one operation.

    This is a git workflow orchestration function that combines stage_all_changes()
    and commit_staged_files() workflows into a single operation.

    Args:
        message: Commit message
        project_dir: Path to the project directory containing the git repository

    Returns:
        CommitResult dictionary containing:
        - success: True if staging and commit were both successful, False otherwise
        - commit_hash: Git commit SHA (first 7 characters) if successful, None otherwise
        - error: Error message if failed, None if successful

    Note:
        - First stages all unstaged changes (both modified and untracked files)
        - Then commits the staged files
        - Returns error if either staging or commit phase fails
        - Provides clear error messages indicating which phase failed
        - Requires non-empty commit message (after stripping whitespace)
        - If no unstaged changes exist but staged changes do, will commit staged changes
        - If no changes exist at all, will succeed with no commit hash
    """
    logger.debug(
        "Orchestrating commit all changes workflow with message: %s in %s",
        message,
        project_dir,
    )

    # Validate inputs early (delegate message validation to commit_staged_files)
    if not is_git_repository(project_dir):
        error_msg = f"Directory is not a git repository: {project_dir}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}

    # Check if there are any changes to commit
    status = get_full_status(project_dir)
    if not status["staged"] and not status["modified"] and not status["untracked"]:
        logger.info("No changes to commit")
        return {"success": True, "commit_hash": None, "error": None}

    try:
        # Stage all unstaged changes first (using staging module)
        logger.debug("Staging all unstaged changes")
        staging_result = stage_all_changes(project_dir)

        if not staging_result:
            error_msg = "Failed to stage changes"
            logger.error(error_msg)
            return {"success": False, "commit_hash": None, "error": error_msg}

        logger.debug("Successfully staged all changes, proceeding to commit")

        # Commit the staged files (using commits module)
        commit_result = commit_staged_files(message, project_dir)

        if commit_result["success"]:
            logger.debug(
                "Successfully completed commit all changes workflow with hash %s",
                commit_result["commit_hash"],
            )
        else:
            logger.error(
                "Staging succeeded but commit failed: %s", commit_result["error"]
            )

        # Return the commit result directly (success or failure)
        return commit_result

    except Exception as e:
        error_msg = f"Unexpected error during commit all changes workflow: {e}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}
