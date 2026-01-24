"""Git staging operations for managing staged changes."""

import logging
from pathlib import Path

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _normalize_git_path, _safe_repo_context, logger
from .readers import get_unstaged_changes, is_git_repository


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
    from .core import stage_all_changes_core
    
    logger.debug("Staging all changes in %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    # Get all unstaged changes for logging purposes
    unstaged_changes = get_unstaged_changes(project_dir)
    all_unstaged_files = (
        unstaged_changes["modified"] + unstaged_changes["untracked"]
    )

    # If no unstaged changes, this is a successful no-op
    if not all_unstaged_files:
        logger.debug("No unstaged changes to stage - success")
        return True

    logger.debug(
        "Staging %d unstaged files using git add --all: %s",
        len(all_unstaged_files),
        all_unstaged_files,
    )

    # Use core function for the actual staging
    success = stage_all_changes_core(project_dir)
    
    if success:
        logger.debug(
            "Successfully staged all %d unstaged changes", len(all_unstaged_files)
        )
    
    return success
