"""Git commit operations for creating commits."""

import logging
from pathlib import Path

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import GIT_SHORT_HASH_LENGTH, CommitResult, _safe_repo_context, logger
from .repository import get_staged_changes, is_git_repository
from .staging import stage_all_changes


def commit_staged_files(message: str, project_dir: Path) -> CommitResult:
    """
    Create a commit from currently staged files.

    Args:
        message: Commit message
        project_dir: Path to the project directory containing the git repository

    Returns:
        CommitResult dictionary containing:
        - success: True if commit was created successfully, False otherwise
        - commit_hash: Git commit SHA (first 7 characters) if successful, None otherwise
        - error: Error message if failed, None if successful

    Note:
        - Only commits currently staged files
        - Requires non-empty commit message (after stripping whitespace)
        - Returns commit hash on success
        - Provides error details on failure
        - Uses existing is_git_repository() for validation
        - Uses get_staged_changes() to verify there's content to commit
    """
    logger.debug("Creating commit with message: %s in %s", message, project_dir)

    # Validate inputs
    if not message or not message.strip():
        error_msg = "Commit message cannot be empty or contain only whitespace"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}

    if not is_git_repository(project_dir):
        error_msg = f"Directory is not a git repository: {project_dir}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}

    try:
        # Check if there are staged files to commit
        staged_files = get_staged_changes(project_dir)
        if not staged_files:
            error_msg = "No staged files to commit"
            logger.error(error_msg)
            return {"success": False, "commit_hash": None, "error": error_msg}

        # Create the commit
        with _safe_repo_context(project_dir) as repo:
            commit = repo.index.commit(message.strip())

            # Get short commit hash
            commit_hash = commit.hexsha[:GIT_SHORT_HASH_LENGTH]

            logger.debug(
                "Successfully created commit %s with message: %s",
                commit_hash,
                message.strip(),
            )

            return {"success": True, "commit_hash": commit_hash, "error": None}

    except (InvalidGitRepositoryError, GitCommandError) as e:
        error_msg = f"Git error creating commit: {e}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error creating commit: {e}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}


def commit_all_changes(message: str, project_dir: Path) -> CommitResult:
    """
    Stage all unstaged changes and commit them in one operation.

    This is a convenience function that combines stage_all_changes() and commit_staged_files()
    workflows into a single operation.

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
        - Uses existing stage_all_changes() and commit_staged_files() functions
        - Provides clear error messages indicating which phase failed
        - Requires non-empty commit message (after stripping whitespace)
        - If no unstaged changes exist but staged changes do, will commit staged changes
        - If no changes exist at all, will fail with appropriate error
    """
    logger.debug("Committing all changes with message: %s in %s", message, project_dir)

    # Validate inputs early (delegate message validation to commit_staged_files)
    if not is_git_repository(project_dir):
        error_msg = f"Directory is not a git repository: {project_dir}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}

    try:
        # Stage all unstaged changes first
        logger.debug("Staging all unstaged changes")
        staging_result = stage_all_changes(project_dir)

        if not staging_result:
            error_msg = "Failed to stage changes"
            logger.error(error_msg)
            return {"success": False, "commit_hash": None, "error": error_msg}

        logger.debug("Successfully staged all changes, proceeding to commit")

        # Commit the staged files
        commit_result = commit_staged_files(message, project_dir)

        if commit_result["success"]:
            logger.debug(
                "Successfully committed all changes with hash %s",
                commit_result["commit_hash"],
            )
        else:
            logger.error(
                "Staging succeeded but commit failed: %s", commit_result["error"]
            )

        # Return the commit result directly (success or failure)
        return commit_result

    except Exception as e:
        error_msg = f"Unexpected error during commit all changes: {e}"
        logger.error(error_msg)
        return {"success": False, "commit_hash": None, "error": error_msg}
