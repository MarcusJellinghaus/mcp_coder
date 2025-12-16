"""Branch operations for git repositories."""

import logging
import re
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .repository import is_git_repository


def get_current_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the current active branch.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        Current branch name as string, or None if:
        - Directory is not a git repository
        - Repository is in detached HEAD state
        - Error occurs during branch detection

    Note:
        Uses existing is_git_repository() validation and follows
        established error handling patterns from other functions.
    """
    logger.debug("Getting current branch name for %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return None

    try:
        with _safe_repo_context(project_dir) as repo:
            # Use repo.active_branch to get current branch
            # This will raise TypeError if in detached HEAD state
            current_branch = repo.active_branch.name
            logger.debug("Current branch: %s", current_branch)
            return current_branch

    except TypeError:
        # Detached HEAD state - repo.active_branch raises TypeError
        logger.debug("Repository is in detached HEAD state")
        return None
    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error getting current branch name: %s", e)
        return None
    except Exception as e:
        logger.warning("Unexpected error getting current branch name: %s", e)
        return None


def get_default_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the default branch from git remote HEAD reference.

    This checks what git considers the default branch by looking at
    refs/remotes/origin/HEAD, which is the authoritative source for
    the remote's default branch setting. If origin/HEAD is not set up
    (common in test environments), falls back to checking for common
    default branch names.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        Default branch name as string, or None if:
        - Directory is not a git repository
        - No remote origin configured and no local default branches found
        - Error occurs during branch detection

    Note:
        Prefers git symbolic-ref as the authoritative source, but provides
        minimal fallback for test environments where origin/HEAD isn't configured.
    """
    logger.debug("Getting default branch name for %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return None

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if origin remote exists
            if "origin" not in [remote.name for remote in repo.remotes]:
                logger.debug("No origin remote found in %s", project_dir)
                # No origin remote, check for local main/master branches
                result = _check_local_default_branches(repo)
                return result

            # Check symbolic ref for origin/HEAD (authoritative source)
            try:
                # This shows what the remote considers the default branch
                result = str(repo.git.symbolic_ref("refs/remotes/origin/HEAD"))
                # Result looks like: "refs/remotes/origin/main"
                if result.startswith("refs/remotes/origin/"):
                    default_branch = result.replace("refs/remotes/origin/", "")
                    logger.debug(
                        "Found default branch from symbolic-ref: %s", default_branch
                    )
                    return default_branch
            except GitCommandError:
                # origin/HEAD not set, try minimal fallback
                logger.debug(
                    "origin/HEAD not set, checking for common default branches"
                )
                result = _check_local_default_branches(repo)
                return result

            # If we reach here, the symbolic-ref command succeeded but didn't match expected format
            logger.debug("Unexpected symbolic-ref format, checking fallback")
            result = _check_local_default_branches(repo)
            return result

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error getting default branch name: %s", e)
        return None
    except Exception as e:
        logger.warning("Unexpected error getting default branch name: %s", e)
        return None


def _check_local_default_branches(repo: Repo) -> Optional[str]:
    """
    Check for common default branch names in local repository.

    Args:
        repo: GitPython repository object

    Returns:
        First found default branch name ("main" or "master"), or None
    """
    # Check for common default branch names
    default_candidates = ["main", "master"]

    try:
        # Get list of all branch names
        branch_names = [branch.name for branch in repo.branches]
        logger.debug("Available local branches: %s", branch_names)

        # Check for default candidates in order of preference
        for candidate in default_candidates:
            if candidate in branch_names:
                logger.debug("Found local default branch: %s", candidate)
                return candidate

        logger.debug("No common default branches found in local repository")
        return None

    except GitCommandError as e:
        logger.debug("Git error checking local branches: %s", e)
        return None


def get_parent_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the parent branch (main or master).

    This is a simple heuristic that returns the main branch as the parent branch.
    In real-world scenarios, determining the actual parent branch is complex and
    would require analyzing git history, but this provides a reasonable default.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        Parent branch name as string ("main" or "master"), or None if:
        - Directory is not a git repository
        - Neither "main" nor "master" branch exists
        - Error occurs during branch detection

    Note:
        Delegates all validation and error handling to get_default_branch_name().
        Uses existing logging patterns from other functions.
    """
    logger.debug("Getting parent branch name for %s", project_dir)

    # Use simple heuristic: call get_default_branch_name() internally
    # This delegates all validation and error handling
    main_branch = get_default_branch_name(project_dir)

    if main_branch:
        logger.debug("Parent branch identified as: %s", main_branch)
    else:
        logger.debug("No main branch found, cannot determine parent branch")

    return main_branch


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
    if not branch_name or not branch_name.strip():
        logger.error("Branch name cannot be empty")
        return False

    # Basic branch name validation (GitHub-compatible)
    invalid_chars = ["~", "^", ":", "?", "*", "["]
    if any(char in branch_name for char in invalid_chars):
        logger.error(
            "Invalid branch name: '%s'. Contains invalid characters", branch_name
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


def branch_exists(project_dir: Path, branch_name: str) -> bool:
    """Check if a git branch exists locally.

    Args:
        project_dir: Path to the project directory containing git repository
        branch_name: Name of the branch to check

    Returns:
        True if branch exists locally, False otherwise
    """
    logger.debug("Checking if branch '%s' exists in %s", branch_name, project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate branch name
    if not branch_name or not branch_name.strip():
        logger.debug("Branch name is empty")
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Get list of local branch names
            existing_branches = [branch.name for branch in repo.branches]
            exists = branch_name in existing_branches

            if exists:
                logger.debug("Branch '%s' exists locally", branch_name)
            else:
                logger.debug("Branch '%s' does not exist locally", branch_name)

            return exists

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error checking branch existence: %s", e)
        return False
    except Exception as e:
        logger.warning("Unexpected error checking branch existence: %s", e)
        return False


def remote_branch_exists(project_dir: Path, branch_name: str) -> bool:
    """Check if a git branch exists on the remote origin.

    Args:
        project_dir: Path to the project directory containing git repository
        branch_name: Name of the branch to check (without 'origin/' prefix)

    Returns:
        True if branch exists on origin remote, False otherwise
    """
    logger.debug(
        "Checking if remote branch '%s' exists in %s", branch_name, project_dir
    )

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate branch name
    if not branch_name or not branch_name.strip():
        logger.debug("Branch name is empty")
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if origin remote exists
            if "origin" not in [remote.name for remote in repo.remotes]:
                logger.debug("No origin remote found in %s", project_dir)
                return False

            # Get remote refs
            remote_refs = [ref.name for ref in repo.remotes.origin.refs]
            remote_branch_name = f"origin/{branch_name}"
            exists = remote_branch_name in remote_refs

            if exists:
                logger.debug("Remote branch '%s' exists", remote_branch_name)
            else:
                logger.debug("Remote branch '%s' does not exist", remote_branch_name)

            return exists

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error checking remote branch existence: %s", e)
        return False
    except Exception as e:
        logger.warning("Unexpected error checking remote branch existence: %s", e)
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


def extract_issue_number_from_branch(branch_name: str) -> Optional[int]:
    """Extract issue number from branch name pattern '{issue_number}-title'.

    Args:
        branch_name: Branch name to extract issue number from

    Returns:
        Issue number as integer if found, None otherwise

    Example:
        >>> extract_issue_number_from_branch("123-feature-name")
        123
        >>> extract_issue_number_from_branch("feature-branch")
        None
    """
    if not branch_name:
        return None
    match = re.match(r"^(\d+)-", branch_name)
    if match:
        return int(match.group(1))
    return None
