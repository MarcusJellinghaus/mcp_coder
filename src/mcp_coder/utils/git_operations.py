"""Git operations utilities for file system operations."""

import logging
from pathlib import Path
from typing import Any, Optional, TypedDict

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

# Use same logging pattern as existing modules (see file_operations.py)
logger = logging.getLogger(__name__)

# Constants for git operations
PLACEHOLDER_HASH = "0" * 7
GIT_SHORT_HASH_LENGTH = 7


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
        Repo(project_dir, search_parent_directories=False)
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
        repo = Repo(project_dir, search_parent_directories=False)

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
        repo = Repo(project_dir, search_parent_directories=False)

        # Get git-compatible paths
        try:
            source_git = _normalize_git_path(source_path, project_dir)
            dest_git = _normalize_git_path(dest_path, project_dir)
        except ValueError as e:
            logger.error("Paths must be within project directory: %s", e)
            return False

        # Execute git mv command
        logger.info("Executing git mv from %s to %s", source_git, dest_git)
        repo.git.mv(source_git, dest_git)

        logger.info(
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
        repo = Repo(project_dir, search_parent_directories=False)

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
        repo = Repo(project_dir, search_parent_directories=False)

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
        repo = Repo(project_dir, search_parent_directories=False)

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
                    "File %s is outside project directory %s", file_path, project_dir
                )
                return False

        # Stage all files at once
        logger.debug("Staging files: %s", relative_paths)
        repo.index.add(relative_paths)

        logger.info(
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
        repo = Repo(project_dir, search_parent_directories=False)

        logger.debug(
            "Staging %d unstaged files using git add --all: %s",
            len(all_unstaged_files),
            all_unstaged_files,
        )

        # Use git add --all to stage all changes (additions, modifications, deletions)
        repo.git.add("--all")

        logger.info(
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
        repo = Repo(project_dir, search_parent_directories=False)
        commit = repo.index.commit(message.strip())

        # Get short commit hash
        commit_hash = commit.hexsha[:GIT_SHORT_HASH_LENGTH]

        logger.info(
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
            logger.info(
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
        repo = Repo(project_dir, search_parent_directories=False)

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
                staged_diff = repo.git.diff("--cached", "--unified=5", "--no-prefix")
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
        repo = Repo(project_dir, search_parent_directories=False)

        # Get current branch name
        current_branch = repo.active_branch.name
        logger.debug("Current branch: %s", current_branch)

        # Execute git push origin <current_branch>
        repo.git.push("origin", current_branch)

        logger.info("Successfully pushed branch '%s' to origin", current_branch)
        return {"success": True, "error": None}

    except (InvalidGitRepositoryError, GitCommandError) as e:
        error_msg = f"Git error during push: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during push: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
