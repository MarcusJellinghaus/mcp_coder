"""Branch operations for git repositories."""

from pathlib import Path
from typing import Optional, Tuple

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .readers import (
    get_current_branch_name,
    get_default_branch_name,
    is_git_repository,
    validate_branch_name,
)
from .remotes import fetch_remote


def create_branch(
    branch_name: str, project_dir: Path, from_branch: Optional[str] = None
) -> bool:
    """Create a new git branch.

    Args:
        branch_name: Name of the branch to create
        project_dir: Path to the project directory containing git repository
        from_branch: Base branch to create from (defaults to current branch)

    Returns:
        True if branch was created successfully, False otherwise
    """
    logger.debug("Creating branch '%s' in %s", branch_name, project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate branch name
    if not validate_branch_name(branch_name):
        logger.error(
            "Invalid branch name: '%s'. Must be non-empty and cannot contain: ~ ^ : ? * [",
            branch_name,
        )
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if branch already exists
            existing_branches = [branch.name for branch in repo.branches]
            if branch_name in existing_branches:
                logger.debug("Branch '%s' already exists", branch_name)
                return False

            # Create new branch
            if from_branch:
                # Create from specified base branch
                try:
                    repo.git.checkout("-b", branch_name, from_branch)
                except GitCommandError as e:
                    logger.error(
                        "Failed to create branch from '%s': %s", from_branch, e
                    )
                    return False
            else:
                # Create from current branch
                try:
                    repo.git.checkout("-b", branch_name)
                except GitCommandError as e:
                    logger.error("Failed to create branch: %s", e)
                    return False

            logger.debug("Successfully created branch '%s'", branch_name)
            return True

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error creating branch: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error creating branch: %s", e)
        return False


def checkout_branch(branch_name: str, project_dir: Path) -> bool:
    """Checkout an existing git branch, creating from remote if needed.

    Args:
        branch_name: Name of the branch to checkout
        project_dir: Path to the project directory containing git repository

    Returns:
        True if branch was checked out successfully, False otherwise

    Note:
        If branch doesn't exist locally but exists on origin remote,
        will create a local tracking branch and check it out.
    """
    logger.debug("Checking out branch '%s' in %s", branch_name, project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate branch name
    if not branch_name or not branch_name.strip():
        logger.error("Branch name cannot be empty")
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if we're already on the target branch
            try:
                current_branch = repo.active_branch.name
                if current_branch == branch_name:
                    logger.debug("Already on branch '%s'", branch_name)
                    return True
            except TypeError:
                # In detached HEAD state, continue with checkout
                pass

            # Check if branch exists locally
            existing_branches = [branch.name for branch in repo.branches]
            branch_exists_locally = branch_name in existing_branches

            if not branch_exists_locally:
                # Check if branch exists on remote
                logger.debug(
                    "Branch '%s' not found locally, checking remote...", branch_name
                )

                # Fetch remote branches to ensure we have latest
                try:
                    if "origin" in [remote.name for remote in repo.remotes]:
                        repo.remotes.origin.fetch()
                        logger.debug("Fetched latest from origin")
                    else:
                        logger.error("No origin remote found")
                        return False
                except GitCommandError as e:
                    logger.error("Failed to fetch from origin: %s", e)
                    return False

                # Check remote branches
                remote_branches = [ref.name for ref in repo.remotes.origin.refs]
                remote_branch_name = f"origin/{branch_name}"

                if remote_branch_name in remote_branches:
                    logger.debug("Found branch on remote: %s", remote_branch_name)
                    # Create local tracking branch and checkout
                    try:
                        repo.git.checkout("-b", branch_name, remote_branch_name)
                        logger.debug(
                            "Created local tracking branch '%s' from '%s'",
                            branch_name,
                            remote_branch_name,
                        )
                        return True
                    except GitCommandError as e:
                        logger.error("Failed to create tracking branch: %s", e)
                        return False
                else:
                    logger.error(
                        "Branch '%s' does not exist locally or on remote", branch_name
                    )
                    return False

            # Branch exists locally, checkout directly
            try:
                repo.git.checkout(branch_name)
                logger.debug("Successfully checked out branch '%s'", branch_name)
                return True
            except GitCommandError as e:
                logger.error("Failed to checkout branch '%s': %s", branch_name, e)
                return False

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error checking out branch: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error checking out branch: %s", e)
        return False


def delete_branch(
    branch_name: str,
    project_dir: Path,
    force: bool = False,
    delete_remote: bool = False,
) -> bool:
    """Delete a git branch locally and optionally from remote.

    Args:
        branch_name: Name of the branch to delete
        project_dir: Path to the project directory containing git repository
        force: If True, force delete even if branch is not fully merged (default: False)
        delete_remote: If True, also delete the branch from remote origin (default: False)

    Returns:
        True if branch was deleted successfully, False otherwise

    Note:
        - Cannot delete the currently active branch (will return False)
        - With force=False, deletion fails if branch has unmerged changes
        - With delete_remote=True, will attempt to delete from origin remote
    """
    logger.debug(
        "Deleting branch '%s' in %s (force=%s, remote=%s)",
        branch_name,
        project_dir,
        force,
        delete_remote,
    )

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate branch name
    if not branch_name or not branch_name.strip():
        logger.error("Branch name cannot be empty")
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if branch exists
            existing_branches = [branch.name for branch in repo.branches]
            if branch_name not in existing_branches:
                logger.debug("Branch '%s' does not exist locally", branch_name)
                return False

            # Cannot delete the currently active branch
            try:
                current_branch = repo.active_branch.name
                if current_branch == branch_name:
                    logger.error(
                        "Cannot delete currently active branch '%s'", branch_name
                    )
                    return False
            except TypeError:
                # In detached HEAD state, can proceed
                pass

            # Delete local branch
            try:
                if force:
                    repo.git.branch("-D", branch_name)
                    logger.debug("Force deleted local branch '%s'", branch_name)
                else:
                    repo.git.branch("-d", branch_name)
                    logger.debug("Deleted local branch '%s'", branch_name)
            except GitCommandError as e:
                logger.error("Failed to delete local branch '%s': %s", branch_name, e)
                return False

            # Delete remote branch if requested
            if delete_remote:
                try:
                    if "origin" in [remote.name for remote in repo.remotes]:
                        repo.git.push("origin", "--delete", branch_name)
                        logger.debug("Deleted remote branch 'origin/%s'", branch_name)
                    else:
                        logger.debug("No origin remote found, skipping remote deletion")
                except GitCommandError as e:
                    # Remote branch might not exist or already deleted
                    logger.debug("Could not delete remote branch: %s", e)
                    # Don't fail the operation if remote deletion fails

            logger.debug("Successfully deleted branch '%s'", branch_name)
            return True

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error deleting branch: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error deleting branch: %s", e)
        return False


def needs_rebase(
    project_dir: Path, target_branch: Optional[str] = None
) -> Tuple[bool, str]:
    """Detect if current branch needs rebasing onto target branch.

    Args:
        project_dir: Path to git repository
        target_branch: Branch to check against (defaults to auto-detect)

    Returns:
        (needs_rebase, reason) where:
        - needs_rebase: True if rebase is needed, False otherwise
        - reason: Description of status ("up-to-date", "3 commits behind", "error: <reason>")
    """
    logger.debug("Checking if rebase needed in %s", project_dir)

    if not is_git_repository(project_dir):
        error_msg = "not a git repository"
        logger.debug("Not a git repository: %s", project_dir)
        return False, f"error: {error_msg}"

    try:
        # Fetch from remote to ensure we have latest refs
        if not fetch_remote(project_dir):
            error_msg = "failed to fetch from remote"
            logger.warning("Failed to fetch from remote for rebase check")
            return False, f"error: {error_msg}"

        with _safe_repo_context(project_dir) as repo:
            # Get current branch
            current_branch = get_current_branch_name(project_dir)
            if not current_branch:
                error_msg = "not on a branch (detached HEAD)"
                logger.debug("Repository is in detached HEAD state")
                return False, f"error: {error_msg}"

            # Determine target branch
            if target_branch is None:
                target_branch = get_default_branch_name(project_dir)
                if not target_branch:
                    error_msg = "cannot determine target branch"
                    logger.debug("Could not determine default branch")
                    return False, f"error: {error_msg}"

            # Don't check rebase against self
            if current_branch == target_branch:
                logger.debug("Current branch is the target branch")
                return False, "up-to-date"

            # Check if origin/target_branch exists
            origin_target = f"origin/{target_branch}"
            try:
                repo.git.rev_parse("--verify", origin_target)
            except GitCommandError:
                error_msg = f"target branch '{origin_target}' not found"
                logger.debug("Target branch not found: %s", origin_target)
                return False, f"error: {error_msg}"

            # Count commits that origin/target has but HEAD doesn't
            try:
                commit_range = f"HEAD..{origin_target}"
                commit_count_output = repo.git.rev_list("--count", commit_range)
                commit_count = int(commit_count_output.strip())

                if commit_count == 0:
                    # No commits in origin/target that aren't in HEAD
                    logger.debug("Current branch is up-to-date with %s", origin_target)
                    return False, "up-to-date"
                elif commit_count == 1:
                    reason = "1 commit behind"
                else:
                    reason = f"{commit_count} commits behind"

                logger.debug(
                    "Current branch is %s %s",
                    commit_count,
                    "commit" if commit_count == 1 else "commits",
                )
                return True, reason

            except (GitCommandError, ValueError) as e:
                error_msg = f"failed to count commits: {e}"
                logger.warning("Failed to count commits for rebase check: %s", e)
                return False, f"error: {error_msg}"

    except (InvalidGitRepositoryError, GitCommandError) as e:
        error_msg = f"git error: {e}"
        logger.error("Git error during rebase check: %s", e)
        return False, f"error: {error_msg}"
    except Exception as e:
        error_msg = f"unexpected error: {e}"
        logger.error("Unexpected error during rebase check: %s", e)
        return False, f"error: {error_msg}"
