"""Git remote operations for push, fetch, and GitHub URL parsing."""

import logging
import re
from pathlib import Path
from typing import Any, Optional

from git.exc import GitCommandError, InvalidGitRepositoryError

from .branches import branch_exists
from .core import _safe_repo_context, logger
from .repository import is_git_repository


def git_push(project_dir: Path) -> dict[str, Any]:
    """
    Push current branch to origin remote.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        Dictionary containing:
        - success: True if push succeeded, False otherwise
        - error: Error message if failed, None if successful
    """
    logger.debug("Pushing current branch to origin for %s", project_dir)

    if not is_git_repository(project_dir):
        error_msg = f"Directory is not a git repository: {project_dir}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    try:
        with _safe_repo_context(project_dir) as repo:
            # Get current branch name
            current_branch = repo.active_branch.name
            logger.debug("Current branch: %s", current_branch)

            # Execute git push origin <current_branch>
            repo.git.push("origin", current_branch)

            logger.debug("Successfully pushed branch '%s' to origin", current_branch)
            return {"success": True, "error": None}

    except (InvalidGitRepositoryError, GitCommandError) as e:
        error_msg = f"Git error during push: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during push: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


def push_branch(branch_name: str, project_dir: Path, set_upstream: bool = True) -> bool:
    """Push a git branch to origin remote.

    Args:
        branch_name: Name of the branch to push
        project_dir: Path to the project directory containing git repository
        set_upstream: Whether to set upstream tracking branch (default: True)

    Returns:
        True if branch was pushed successfully, False otherwise
    """
    logger.debug("Pushing branch '%s' to origin in %s", branch_name, project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate branch name
    if not branch_name or not branch_name.strip():
        logger.error("Branch name cannot be empty")
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if branch exists locally
            if not branch_exists(project_dir, branch_name):
                logger.error("Branch '%s' does not exist locally", branch_name)
                return False

            # Check if origin remote exists
            if "origin" not in [remote.name for remote in repo.remotes]:
                logger.error("No origin remote found")
                return False

            # Push the branch
            try:
                if set_upstream:
                    # Push with upstream tracking
                    repo.git.push("--set-upstream", "origin", branch_name)
                    logger.debug(
                        "Successfully pushed branch '%s' with upstream tracking",
                        branch_name,
                    )
                else:
                    # Push without upstream tracking
                    repo.git.push("origin", branch_name)
                    logger.debug("Successfully pushed branch '%s'", branch_name)

                return True

            except GitCommandError as e:
                logger.error("Failed to push branch '%s': %s", branch_name, e)
                return False

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error pushing branch: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error pushing branch: %s", e)
        return False


def fetch_remote(project_dir: Path, remote: str = "origin") -> bool:
    """Fetch latest changes from remote repository.

    Args:
        project_dir: Path to the project directory containing git repository
        remote: Name of the remote to fetch from (default: "origin")

    Returns:
        True if fetch was successful, False otherwise
    """
    logger.debug("Fetching from remote '%s' in %s", remote, project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Validate remote name
    if not remote or not remote.strip():
        logger.error("Remote name cannot be empty")
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if remote exists
            if remote not in [r.name for r in repo.remotes]:
                logger.error("Remote '%s' not found", remote)
                return False

            # Fetch from remote
            try:
                repo.git.fetch(remote)
                logger.debug("Successfully fetched from remote '%s'", remote)
                return True

            except GitCommandError as e:
                logger.error("Failed to fetch from remote '%s': %s", remote, e)
                return False

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error fetching from remote: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error fetching from remote: %s", e)
        return False


def get_github_repository_url(project_dir: Path) -> Optional[str]:
    """Get GitHub repository URL from git remote origin.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        GitHub repository URL in https format, or None if:
        - Directory is not a git repository
        - No remote origin configured
        - Remote origin is not a GitHub URL
        - Error occurs during URL detection

    Note:
        Converts various Git URL formats to standard GitHub HTTPS format:
        - SSH: git@github.com:owner/repo.git → https://github.com/owner/repo
        - HTTPS: https://github.com/owner/repo.git → https://github.com/owner/repo
    """
    logger.debug("Getting GitHub repository URL for %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return None

    try:
        with _safe_repo_context(project_dir) as repo:
            # Check if origin remote exists
            if "origin" not in [remote.name for remote in repo.remotes]:
                logger.debug("No origin remote found in %s", project_dir)
                return None

            # Get origin remote URL
            origin_url = repo.remotes.origin.url
            logger.debug("Found origin URL: %s", origin_url)

            # Parse and convert to GitHub HTTPS format
            github_url = _parse_github_url(origin_url)
            if github_url:
                logger.debug("Converted to GitHub URL: %s", github_url)
            else:
                logger.debug("Could not parse as GitHub URL: %s", origin_url)

            return github_url

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error getting repository URL: %s", e)
        return None
    except Exception as e:
        logger.warning("Unexpected error getting repository URL: %s", e)
        return None


def _parse_github_url(git_url: str) -> Optional[str]:
    """Parse git URL and convert to GitHub HTTPS format.

    Args:
        git_url: Git remote URL in various formats

    Returns:
        GitHub HTTPS URL or None if not a valid GitHub URL
    """
    # Remove trailing whitespace
    git_url = git_url.strip()

    # Pattern to match GitHub URLs in various formats
    # SSH: git@github.com:owner/repo.git
    # HTTPS: https://github.com/owner/repo.git
    # HTTPS without .git: https://github.com/owner/repo
    github_pattern = (
        r"(?:https://github\.com/|git@github\.com:)([^/]+)/([^/\.]+)(?:\.git)?/?$"
    )
    match = re.match(github_pattern, git_url)

    if not match:
        return None

    owner, repo_name = match.groups()
    return f"https://github.com/{owner}/{repo_name}"
