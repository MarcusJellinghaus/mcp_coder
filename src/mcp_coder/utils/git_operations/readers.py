"""Read-only git operations for repository queries.

This module provides all read-only/query operations for git repositories.
These functions are used by multiple command modules (branches, remotes, etc.)
and form the middle layer of the git_operations architecture.

Architecture:
    Command modules (branches, remotes, commits, etc.) → readers → core
"""

import re
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger

# ============================================================================
# Repository Status Functions
# ============================================================================


def is_git_repository(project_dir: Path) -> bool:
    """
    Check if the project directory is a git repository.

    Args:
        project_dir: Path to check for git repository

    Returns:
        True if the directory is a git repository, False otherwise
    """
    logger.debug("Checking if %s is a git repository", project_dir)

    try:
        with _safe_repo_context(project_dir):
            logger.debug("Detected as git repository: %s", project_dir)
            return True
    except InvalidGitRepositoryError:
        logger.debug("Not a git repository: %s", project_dir)
        return False
    except Exception as e:
        logger.warning("Error checking if directory is git repository: %s", e)
        return False


def get_staged_changes(project_dir: Path) -> list[str]:
    """
    Get list of files currently staged for commit.

    Args:
        project_dir: Path to the project directory

    Returns:
        List of file paths currently staged for commit, relative to project root.
        Returns empty list if no staged files or if not a git repository.
    """
    logger.debug("Getting staged changes for %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return []

    try:
        with _safe_repo_context(project_dir) as repo:
            # Use git diff --cached --name-only to get staged files
            # This shows files that are staged for the next commit
            staged_files = repo.git.diff("--cached", "--name-only").splitlines()

            # Filter out empty strings and ensure we have clean paths
            staged_files = [f for f in staged_files if f.strip()]

            logger.debug("Found %d staged files: %s", len(staged_files), staged_files)
            return staged_files

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error getting staged changes: %s", e)
        return []
    except Exception as e:
        logger.warning("Unexpected error getting staged changes: %s", e)
        return []


def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]:
    """
    Get list of files with unstaged changes (modified and untracked).

    Args:
        project_dir: Path to the project directory

    Returns:
        Dictionary with 'modified' and 'untracked' keys containing lists of file paths.
        File paths are relative to project root.
        Returns empty dict if not a git repository.
    """
    logger.debug("Getting unstaged changes for %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return {"modified": [], "untracked": []}

    try:
        with _safe_repo_context(project_dir) as repo:
            # Use git status --porcelain to get file status
            # Format: XY filename where X=index status, Y=working tree status
            # We want files where Y is not empty (working tree changes)
            # Use -u to show individual untracked files instead of just directories
            status_output = repo.git.status("--porcelain", "-u").splitlines()

            modified_files = []
            untracked_files = []

            for line in status_output:
                if len(line) < 3:
                    continue

                # Parse git status format: XY filename
                index_status = line[0]  # Staged changes  # noqa: F841
                working_status = line[1]  # Working tree changes
                filename = line[3:]  # Skip space and get filename

                # Skip files that are only staged (no working tree changes)
                if working_status == " ":
                    continue

                # Untracked files have '??' status
                if line.startswith("??"):
                    untracked_files.append(filename)
                else:
                    # Any other working tree change (M, D, etc.)
                    modified_files.append(filename)

            logger.debug(
                "Found %d modified and %d untracked files",
                len(modified_files),
                len(untracked_files),
            )

            return {"modified": modified_files, "untracked": untracked_files}

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error getting unstaged changes: %s", e)
        return {"modified": [], "untracked": []}
    except Exception as e:
        logger.warning("Unexpected error getting unstaged changes: %s", e)
        return {"modified": [], "untracked": []}


def get_full_status(project_dir: Path) -> dict[str, list[str]]:
    """
    Get comprehensive status of all changes: staged, modified, and untracked files.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dictionary with 'staged', 'modified', and 'untracked' keys containing lists of file paths.
        File paths are relative to project root.
        Returns empty dict if not a git repository.

    Example:
        {
            "staged": ["new_feature.py", "docs/readme.md"],
            "modified": ["existing_file.py"],
            "untracked": ["temp_notes.txt"]
        }
    """
    logger.debug("Getting full git status for %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return {"staged": [], "modified": [], "untracked": []}

    try:
        # Use existing functions for consistency and efficiency
        staged_files = get_staged_changes(project_dir)
        unstaged_changes = get_unstaged_changes(project_dir)

        result = {
            "staged": staged_files,
            "modified": unstaged_changes["modified"],
            "untracked": unstaged_changes["untracked"],
        }

        logger.debug(
            "Full status: %d staged, %d modified, %d untracked files",
            len(result["staged"]),
            len(result["modified"]),
            len(result["untracked"]),
        )

        return result

    except Exception as e:
        logger.warning("Unexpected error getting full git status: %s", e)
        return {"staged": [], "modified": [], "untracked": []}


def is_working_directory_clean(
    project_dir: Path, ignore_files: list[str] | None = None
) -> bool:
    """
    Check if working directory has no uncommitted changes.

    Args:
        project_dir: Path to the project directory containing git repository
        ignore_files: Optional list of filenames to ignore when checking for changes.
            Files in this list will not be counted as uncommitted changes.
            Useful for auto-generated files like uv.lock.

    Returns:
        True if no staged, modified, or untracked files exist (after filtering), False otherwise

    Raises:
        ValueError: If the directory is not a git repository

    Note:
        Uses existing get_full_status() for consistency
    """
    if not is_git_repository(project_dir):
        raise ValueError(f"Directory is not a git repository: {project_dir}")

    status = get_full_status(project_dir)

    # Filter out ignored files from each category
    if ignore_files:
        ignore_set = set(ignore_files)
        staged = [f for f in status["staged"] if f not in ignore_set]
        modified = [f for f in status["modified"] if f not in ignore_set]
        untracked = [f for f in status["untracked"] if f not in ignore_set]
    else:
        staged = status["staged"]
        modified = status["modified"]
        untracked = status["untracked"]

    total_changes = len(staged) + len(modified) + len(untracked)

    return total_changes == 0


# ============================================================================
# Branch Validation
# ============================================================================


def validate_branch_name(branch_name: str) -> bool:
    """Validate branch name against git naming rules.

    Args:
        branch_name: Branch name to validate

    Returns:
        True if valid, False otherwise

    Validation rules:
        - Must be non-empty string
        - Cannot contain: ~ ^ : ? * [
    """
    # Check for empty or whitespace-only branch name
    if not branch_name or not branch_name.strip():
        return False

    # Basic branch name validation (GitHub-compatible)
    invalid_chars = ["~", "^", ":", "?", "*", "["]
    if any(char in branch_name for char in invalid_chars):
        return False

    return True


# ============================================================================
# Branch Name Readers
# ============================================================================


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


# ============================================================================
# Branch Existence Checks
# ============================================================================


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


# ============================================================================
# Branch Utilities
# ============================================================================


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


# ============================================================================
# Merge-Base Detection
# ============================================================================

# Maximum commits between merge-base and candidate branch HEAD to consider
# the candidate as the parent branch. Higher values are more permissive but
# risk selecting wrong branches; lower values may miss valid parents that
# have moved forward since branching.
MERGE_BASE_DISTANCE_THRESHOLD = 20


def detect_parent_branch_via_merge_base(
    project_dir: Path,
    current_branch: str,
    distance_threshold: int = MERGE_BASE_DISTANCE_THRESHOLD,
) -> Optional[str]:
    """Detect parent branch using git merge-base.

    For each local and remote branch (candidate), find the merge-base with
    current branch. The parent is the branch whose HEAD is closest to the
    merge-base (smallest distance).

    Args:
        project_dir: Path to git repository
        current_branch: Current branch name
        distance_threshold: Maximum commits between merge-base and candidate
            branch HEAD to consider the candidate as the parent branch.
            Defaults to MERGE_BASE_DISTANCE_THRESHOLD (20).

    Returns:
        Branch name if found within threshold, None otherwise
    """
    logger.debug(
        "Detecting parent branch for '%s' via merge-base (threshold=%d)",
        current_branch,
        distance_threshold,
    )

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return None

    try:
        with _safe_repo_context(project_dir) as repo:
            # Get current branch commit
            try:
                current_commit = repo.heads[current_branch].commit
            except (IndexError, KeyError) as e:
                logger.debug(
                    "Failed to get commit for branch '%s': %s", current_branch, e
                )
                return None

            candidates_passing: list[tuple[str, int]] = []
            checked_branch_names: set[str] = set()

            # Check local branches
            for branch in repo.heads:
                if branch.name == current_branch:
                    continue

                try:
                    merge_base_list = repo.merge_base(current_commit, branch.commit)
                    if not merge_base_list:
                        logger.debug(
                            "No merge-base found for local branch '%s'", branch.name
                        )
                        continue

                    merge_base = merge_base_list[0]
                    # Count commits from merge-base to branch HEAD
                    distance = sum(
                        1
                        for _ in repo.iter_commits(
                            f"{merge_base.hexsha}..{branch.commit.hexsha}"
                        )
                    )
                    logger.debug(
                        "Local branch '%s': merge-base distance = %d",
                        branch.name,
                        distance,
                    )

                    # Early exit: distance=0 means ideal parent (branch HEAD is merge-base)
                    if distance == 0:
                        logger.debug(
                            "Detected parent branch from merge-base: '%s' (distance=0)",
                            branch.name,
                        )
                        return branch.name

                    if distance <= distance_threshold:
                        candidates_passing.append((branch.name, distance))
                        checked_branch_names.add(branch.name)

                except GitCommandError as e:
                    logger.debug(
                        "Git error checking local branch '%s': %s", branch.name, e
                    )
                    continue

            # Check remote branches (origin/*)
            try:
                if "origin" in [r.name for r in repo.remotes]:
                    for ref in repo.remotes.origin.refs:
                        # Extract branch name without "origin/" prefix
                        branch_name = ref.name.replace("origin/", "", 1)

                        # Skip current branch, HEAD, and already-checked branches
                        if branch_name in (current_branch, "HEAD"):
                            continue
                        if branch_name in checked_branch_names:
                            continue

                        try:
                            merge_base_list = repo.merge_base(
                                current_commit, ref.commit
                            )
                            if not merge_base_list:
                                logger.debug(
                                    "No merge-base found for remote branch '%s'",
                                    branch_name,
                                )
                                continue

                            merge_base = merge_base_list[0]
                            # Count commits from merge-base to remote branch HEAD
                            distance = sum(
                                1
                                for _ in repo.iter_commits(
                                    f"{merge_base.hexsha}..{ref.commit.hexsha}"
                                )
                            )
                            logger.debug(
                                "Remote branch '%s': merge-base distance = %d",
                                branch_name,
                                distance,
                            )

                            # Early exit: distance=0 means ideal parent
                            if distance == 0:
                                logger.debug(
                                    "Detected parent branch from merge-base: '%s' (distance=0)",
                                    branch_name,
                                )
                                return branch_name

                            if distance <= distance_threshold:
                                candidates_passing.append((branch_name, distance))
                                checked_branch_names.add(branch_name)

                        except GitCommandError as e:
                            logger.debug(
                                "Git error checking remote branch '%s': %s",
                                branch_name,
                                e,
                            )
                            continue
            except Exception as e:
                logger.debug("Error checking remote branches: %s", e)

            # Return smallest distance candidate
            if candidates_passing:
                candidates_passing.sort(key=lambda x: x[1])
                winner = candidates_passing[0]
                logger.debug(
                    "Detected parent branch from merge-base: '%s' (distance=%d)",
                    winner[0],
                    winner[1],
                )
                return winner[0]

            logger.debug("No candidate branches found within threshold")
            return None

    except InvalidGitRepositoryError:
        logger.debug("Invalid git repository: %s", project_dir)
        return None
    except Exception as e:
        logger.debug("Failed to detect parent branch: %s", e)
        return None
