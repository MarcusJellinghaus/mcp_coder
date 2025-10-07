"""Git operations utilities for file system operations."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, TypedDict

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

# Use same logging pattern as existing modules (see file_operations.py)
logger = logging.getLogger(__name__)

# Constants for git operations
PLACEHOLDER_HASH = "0" * 7
GIT_SHORT_HASH_LENGTH = 7


def _close_repo_safely(repo: Repo) -> None:
    """Safely close a GitPython repository to prevent handle leaks on Windows."""
    try:
        # Close any active git command processes
        if hasattr(repo, "git") and hasattr(repo.git, "_proc") and repo.git._proc:
            try:
                if repo.git._proc.poll() is None:  # Process still running
                    repo.git._proc.terminate()
                    import time

                    time.sleep(0.1)
                    if repo.git._proc.poll() is None:  # Still running, force kill
                        repo.git._proc.kill()
            except (OSError, AttributeError):
                pass  # Ignore errors during process cleanup

        # Close the repository if it has a close method
        if hasattr(repo, "close"):
            repo.close()

    except (AttributeError, OSError, Exception) as e:
        # Log but don't raise - cleanup should be best effort
        logger.debug("Error during repository cleanup (non-critical): %s", e)


@contextmanager
def _safe_repo_context(project_dir: Path) -> Iterator[Repo]:
    """Context manager for safely handling GitPython repository objects.

    Ensures proper cleanup of repository objects to prevent Windows handle issues.

    Args:
        project_dir: Path to the git repository directory

    Yields:
        Repo: GitPython repository object

    Raises:
        InvalidGitRepositoryError: If directory is not a git repository
    """
    repo = None
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        yield repo
    finally:
        if repo:
            _close_repo_safely(repo)


def _normalize_git_path(path: Path, base_dir: Path) -> str:
    """Convert a path to git-compatible format.

    Args:
        path: Path to normalize
        base_dir: Base directory to make path relative to

    Returns:
        Git-compatible path string using forward slashes

    Raises:
        ValueError: If path is not relative to base_dir
    """
    relative_path = path.relative_to(base_dir)
    return str(relative_path).replace("\\", "/")


# Type alias for commit result structure
class CommitResult(TypedDict):
    """Result of a git commit operation."""

    success: bool
    commit_hash: Optional[str]
    error: Optional[str]


# Type alias for git push result structure
class PushResult(TypedDict):
    """Result of a git push operation."""

    success: bool
    error: Optional[str]


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


def is_file_tracked(file_path: Path, project_dir: Path) -> bool:
    """
    Check if a file is tracked by git.

    Args:
        file_path: Path to the file to check
        project_dir: Project directory containing the git repository

    Returns:
        True if the file is tracked by git, False otherwise
    """
    if not is_git_repository(project_dir):
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Get git-compatible path
            try:
                git_path = _normalize_git_path(file_path, project_dir)
            except ValueError:
                # File is outside project directory
                logger.debug(
                    "File %s is outside project directory %s", file_path, project_dir
                )
                return False

            # Use git ls-files to check if file is tracked
            # This returns all files that git knows about (staged or committed)
            try:
                # Use ls-files with the specific file to avoid loading all files
                result = repo.git.ls_files(git_path)
                # If git returns the file path, it's tracked
                return bool(result and git_path in result)
            except GitCommandError:
                # File is not tracked
                return False

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug("Git error checking if file is tracked: %s", e)
        return False
    except Exception as e:
        logger.warning("Unexpected error checking if file is tracked: %s", e)
        return False


def git_move(source_path: Path, dest_path: Path, project_dir: Path) -> bool:
    """
    Move a file using git mv command.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        project_dir: Project directory containing the git repository

    Returns:
        True if the file was moved successfully using git, False otherwise

    Raises:
        GitCommandError: If git mv command fails
    """
    if not is_git_repository(project_dir):
        return False

    try:
        with _safe_repo_context(project_dir) as repo:
            # Get git-compatible paths
            try:
                source_git = _normalize_git_path(source_path, project_dir)
                dest_git = _normalize_git_path(dest_path, project_dir)
            except ValueError as e:
                logger.error("Paths must be within project directory: %s", e)
                return False

            # Execute git mv command
            logger.debug("Executing git mv from %s to %s", source_git, dest_git)
            repo.git.mv(source_git, dest_git)

            logger.debug(
                "Successfully moved file using git from %s to %s", source_git, dest_git
            )
            return True

    except GitCommandError as e:
        logger.error("Git move failed: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error during git move: %s", e)
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
                index_status = line[0]  # Staged changes
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


def stage_specific_files(files: list[Path], project_dir: Path) -> bool:
    """
    Stage specific files for commit.

    Args:
        files: List of file paths to stage
        project_dir: Path to the project directory containing the git repository

    Returns:
        True if all specified files were staged successfully, False otherwise

    Note:
        - Handles both absolute and relative file paths
        - Validates files exist and are within project directory
        - Logs appropriate warnings/errors for failed operations
        - Returns False if any files couldn't be staged (all-or-nothing approach)
    """
    logger.debug("Staging %d specific files in %s", len(files), project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Handle empty list - this is a valid no-op case
    if not files:
        logger.debug("No files to stage - success")
        return True

    try:
        with _safe_repo_context(project_dir) as repo:
            # Validate and convert all file paths first
            relative_paths = []
            for file_path in files:
                # Check if file exists
                if not file_path.exists():
                    logger.error("File does not exist: %s", file_path)
                    return False

                # Get git-compatible path
                try:
                    git_path = _normalize_git_path(file_path, project_dir)
                    relative_paths.append(git_path)
                except ValueError:
                    logger.error(
                        "File %s is outside project directory %s",
                        file_path,
                        project_dir,
                    )
                    return False

            # Stage all files at once
            logger.debug("Staging files: %s", relative_paths)
            repo.index.add(relative_paths)

            logger.debug(
                "Successfully staged %d files: %s", len(relative_paths), relative_paths
            )
            return True

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error staging files: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error staging files: %s", e)
        return False


def stage_all_changes(project_dir: Path) -> bool:
    """
    Stage all unstaged changes (both modified and untracked files) for commit.

    Args:
        project_dir: Path to the project directory containing the git repository

    Returns:
        True if all unstaged changes were staged successfully, False otherwise

    Note:
        - Stages both modified tracked files (including deletions) and untracked files
        - Returns True if no unstaged changes exist (no-op case)
        - Uses git add --all to handle deletions properly
        - Returns False if staging operation fails
    """
    logger.debug("Staging all changes in %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    try:
        # Get all unstaged changes
        unstaged_changes = get_unstaged_changes(project_dir)

        # Combine modified and untracked files
        all_unstaged_files = (
            unstaged_changes["modified"] + unstaged_changes["untracked"]
        )

        # If no unstaged changes, this is a successful no-op
        if not all_unstaged_files:
            logger.debug("No unstaged changes to stage - success")
            return True

        # Use git add --all to stage everything including deletions
        # This is more robust than trying to handle individual files
        with _safe_repo_context(project_dir) as repo:
            logger.debug(
                "Staging %d unstaged files using git add --all: %s",
                len(all_unstaged_files),
                all_unstaged_files,
            )

            # Use git add --all to stage all changes (additions, modifications, deletions)
            repo.git.add("--all")

            logger.debug(
                "Successfully staged all %d unstaged changes", len(all_unstaged_files)
            )

            return True

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error staging all changes: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error staging all changes: %s", e)
        return False


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


def _generate_untracked_diff(repo: Repo, project_dir: Path) -> str:
    """Generate diff for untracked files by creating synthetic diff output."""
    try:
        untracked_files = repo.untracked_files
        if not untracked_files:
            return ""

        untracked_diffs = []
        for file_path in untracked_files:
            try:
                # Read the file content
                full_path = project_dir / file_path
                if full_path.exists() and full_path.is_file():
                    # Create a synthetic diff that looks like git's output
                    try:
                        content = full_path.read_text(encoding="utf-8")
                        lines = content.splitlines()

                        # Create git-style diff header
                        diff_lines = [
                            f"diff --git {file_path} {file_path}",
                            "new file mode 100644",
                            f"index 0000000..{PLACEHOLDER_HASH}",
                            "--- /dev/null",
                            f"+++ {file_path}",
                            "@@ -0,0 +1," + str(len(lines)) + " @@",
                        ]

                        # Add file content with + prefix
                        for line in lines:
                            diff_lines.append("+" + line)

                        untracked_diffs.append("\n".join(diff_lines))
                    except UnicodeDecodeError:
                        # Handle binary files
                        diff_lines = [
                            f"diff --git {file_path} {file_path}",
                            "new file mode 100644",
                            f"index 0000000..{PLACEHOLDER_HASH}",
                            "Binary files /dev/null and " + file_path + " differ",
                        ]
                        untracked_diffs.append("\n".join(diff_lines))
            except Exception as e:
                # Skip individual files that can't be processed
                logger.debug(
                    "Skipping untracked file that couldn't be processed: %s - %s",
                    file_path,
                    e,
                )
                continue

        return "\n".join(untracked_diffs)

    except Exception as e:
        logger.warning("Error generating untracked file diff: %s", e)
        return ""


def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """
    Generate comprehensive git diff without modifying repository state.

    Shows staged, unstaged, and untracked files in unified diff format
    suitable for LLM analysis and commit message generation.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        str: Unified diff format with sections for staged changes, unstaged
             changes, and untracked files. Each section uses format:
             === SECTION NAME ===
             [diff content]

             Returns empty string if no changes detected.
        None: If error occurs (invalid repository, git command failure, etc.)

    Example:
        >>> diff_output = get_git_diff_for_commit(Path("/path/to/repo"))
        >>> if diff_output is not None:
        ...     print("Changes detected" if diff_output else "No changes")

    Note:
        - Uses read-only git operations, never modifies repository state
        - Binary files handled naturally by git (shows "Binary files differ")
        - Continues processing even if individual git operations fail
        - Empty repositories (no commits) supported
    """
    logger.debug("Generating git diff for: %s", project_dir)

    if not is_git_repository(project_dir):
        logger.error("Not a git repository: %s", project_dir)
        return None

    try:
        with _safe_repo_context(project_dir) as repo:
            # Simple check for empty repository (KISS approach)
            has_commits = True
            try:
                list(repo.iter_commits(max_count=1))
            except (GitCommandError, ValueError):
                has_commits = False
                logger.debug("Empty repository detected, showing untracked files only")

            # Generate diff sections with individual error handling
            staged_diff = ""
            unstaged_diff = ""

            if has_commits:
                try:
                    staged_diff = repo.git.diff(
                        "--cached", "--unified=5", "--no-prefix"
                    )
                except GitCommandError as e:
                    logger.warning("Failed to get staged diff: %s", e)

                try:
                    unstaged_diff = repo.git.diff("--unified=5", "--no-prefix")
                except GitCommandError as e:
                    logger.warning("Failed to get unstaged diff: %s", e)

            # Always try to get untracked files
            untracked_diff = _generate_untracked_diff(repo, project_dir)

            return _format_diff_sections(staged_diff, unstaged_diff, untracked_diff)

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error generating diff: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error generating diff: %s", e)
        return None


def _format_diff_sections(
    staged_diff: str, unstaged_diff: str, untracked_diff: str
) -> str:
    """Format diff sections with appropriate headers."""
    sections = []

    if staged_diff.strip():
        sections.append(f"=== STAGED CHANGES ===\n{staged_diff}")

    if unstaged_diff.strip():
        sections.append(f"=== UNSTAGED CHANGES ===\n{unstaged_diff}")

    if untracked_diff.strip():
        sections.append(f"=== UNTRACKED FILES ===\n{untracked_diff}")

    return "\n\n".join(sections)


def is_working_directory_clean(project_dir: Path) -> bool:
    """
    Check if working directory has no uncommitted changes.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        True if no staged, modified, or untracked files exist, False otherwise

    Raises:
        ValueError: If the directory is not a git repository

    Note:
        Uses existing get_full_status() for consistency
    """
    if not is_git_repository(project_dir):
        raise ValueError(f"Directory is not a git repository: {project_dir}")

    status = get_full_status(project_dir)
    total_changes = (
        len(status["staged"]) + len(status["modified"]) + len(status["untracked"])
    )

    return total_changes == 0


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


def get_branch_diff(
    project_dir: Path,
    base_branch: Optional[str] = None,
    exclude_paths: Optional[list[str]] = None,
) -> str:
    """Generate git diff between current branch and base branch.

    Args:
        project_dir: Path to the project directory containing git repository
        base_branch: Base branch to compare against (auto-detected if None)
        exclude_paths: List of paths to exclude from diff (e.g., ['pr_info/', '*.log'])

    Returns:
        Git diff string between base branch and current HEAD, or empty string on error

    Note:
        - Uses three-dot notation (base...HEAD) to show changes on current branch
        - Auto-detects base branch using get_parent_branch_name() if not provided
        - Returns empty string for any error conditions (invalid repo, missing branch, etc.)
        - Uses unified diff format with 5 lines of context
    """
    logger.debug(
        "Getting branch diff for %s (base: %s, excludes: %s)",
        project_dir,
        base_branch,
        exclude_paths,
    )

    # Validate repository
    if not is_git_repository(project_dir):
        logger.error("Directory %s is not a git repository", project_dir)
        return ""

    try:
        with _safe_repo_context(project_dir) as repo:
            # Auto-detect base branch if not provided
            if base_branch is None:
                base_branch = get_parent_branch_name(project_dir)
                if base_branch is None:
                    logger.error("Could not determine base branch for diff")
                    return ""
                logger.debug("Auto-detected base branch: %s", base_branch)

            # Get current branch for validation
            current_branch = get_current_branch_name(project_dir)
            if current_branch is None:
                logger.error("Could not determine current branch")
                return ""

            # Check if current branch is the base branch
            if current_branch == base_branch:
                logger.debug("Current branch is the base branch, no diff to show")
                return ""

            # Verify base branch exists
            if not branch_exists(project_dir, base_branch):
                logger.error("Base branch '%s' does not exist", base_branch)
                return ""

            # Build git diff command
            if exclude_paths:
                # When using exclusions, we need to construct the command differently
                # git diff base...HEAD -- . ':!excluded_path'
                diff_args = [
                    f"{base_branch}...HEAD",
                    "--unified=5",
                    "--no-prefix",
                    "--",
                    ".",
                ]
                for path in exclude_paths:
                    # Use pathspec magic to exclude paths
                    diff_args.append(f":!{path}")
            else:
                # Simple diff without exclusions
                diff_args = [
                    f"{base_branch}...HEAD",
                    "--unified=5",
                    "--no-prefix",
                ]

            # Execute git diff with UTF-8 encoding environment
            # Set environment for this process to handle UTF-8 properly
            import os

            original_env = {}
            encoding_vars = {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
            # Only set LC_ALL on non-Windows systems
            if os.name != "nt":
                encoding_vars["LC_ALL"] = "C.UTF-8"

            # Store original values and set new ones
            for key, value in encoding_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                # Execute git diff with encoding environment set
                diff_output = repo.git.diff(*diff_args)
            finally:
                # Restore original environment
                for key, original_value in original_env.items():
                    if original_value is not None:
                        os.environ[key] = original_value
                    else:
                        os.environ.pop(key, None)

            logger.debug(
                "Generated diff between %s and %s (%d bytes)",
                base_branch,
                current_branch,
                len(diff_output),
            )

            return str(diff_output)

    except GitCommandError as e:
        logger.error("Git command error generating diff: %s", e)
        return ""
    except Exception as e:
        logger.error("Unexpected error generating diff: %s", e)
        return ""


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
    """Checkout an existing git branch.

    Args:
        branch_name: Name of the branch to checkout
        project_dir: Path to the project directory containing git repository

    Returns:
        True if branch was checked out successfully, False otherwise
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
            # Check if branch exists locally
            existing_branches = [branch.name for branch in repo.branches]
            if branch_name not in existing_branches:
                logger.error("Branch '%s' does not exist locally", branch_name)
                return False

            # Check if we're already on the target branch
            try:
                current_branch = repo.active_branch.name
                if current_branch == branch_name:
                    logger.debug("Already on branch '%s'", branch_name)
                    return True
            except TypeError:
                # In detached HEAD state, continue with checkout
                pass

            # Checkout the branch
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


def _parse_github_url(git_url: str) -> Optional[str]:
    """Parse git URL and convert to GitHub HTTPS format.

    Args:
        git_url: Git remote URL in various formats

    Returns:
        GitHub HTTPS URL or None if not a valid GitHub URL
    """
    import re

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


# Explicit exports for mypy
__all__ = [
    "CommitResult",
    "PushResult",
    "branch_exists",
    "checkout_branch",
    "commit_all_changes",
    "commit_staged_files",
    "create_branch",
    "fetch_remote",
    "get_branch_diff",
    "get_current_branch_name",
    "get_default_branch_name",
    "get_full_status",
    "get_git_diff_for_commit",
    "get_github_repository_url",
    "get_parent_branch_name",
    "get_staged_changes",
    "get_unstaged_changes",
    "git_move",
    "git_push",
    "is_file_tracked",
    "is_git_repository",
    "is_working_directory_clean",
    "push_branch",
    "stage_all_changes",
    "stage_specific_files",
]
