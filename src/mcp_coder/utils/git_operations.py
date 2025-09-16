"""Git operations utilities for file system operations."""

import logging
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

# Use same logging pattern as existing modules (see file_operations.py)
logger = logging.getLogger(__name__)


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

        # Get relative path from project directory
        try:
            relative_path = file_path.relative_to(project_dir)
        except ValueError:
            # File is outside project directory
            logger.debug(
                "File %s is outside project directory %s", file_path, project_dir
            )
            return False

        # Convert to posix path for git (even on Windows)
        git_path = str(relative_path).replace("\\", "/")

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

        # Get relative paths from project directory
        try:
            source_relative = source_path.relative_to(project_dir)
            dest_relative = dest_path.relative_to(project_dir)
        except ValueError as e:
            logger.error("Paths must be within project directory: %s", e)
            return False

        # Convert to posix paths for git
        source_git = str(source_relative).replace("\\", "/")
        dest_git = str(dest_relative).replace("\\", "/")

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
            if working_status == ' ':
                continue
                
            # Untracked files have '??' status
            if line.startswith('??'):
                untracked_files.append(filename)
            else:
                # Any other working tree change (M, D, etc.)
                modified_files.append(filename)
        
        logger.debug(
            "Found %d modified and %d untracked files", 
            len(modified_files), 
            len(untracked_files)
        )
        
        return {
            "modified": modified_files,
            "untracked": untracked_files
        }

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
            "untracked": unstaged_changes["untracked"]
        }
        
        logger.debug(
            "Full status: %d staged, %d modified, %d untracked files",
            len(result["staged"]),
            len(result["modified"]),
            len(result["untracked"])
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
            
            # Get relative path from project directory
            try:
                relative_path = file_path.relative_to(project_dir)
            except ValueError:
                logger.error(
                    "File %s is outside project directory %s", 
                    file_path, project_dir
                )
                return False
            
            # Convert to posix path for git (even on Windows)
            git_path = str(relative_path).replace("\\", "/")
            relative_paths.append(git_path)
        
        # Stage all files at once
        logger.debug("Staging files: %s", relative_paths)
        repo.index.add(relative_paths)
        
        logger.info(
            "Successfully staged %d files: %s", 
            len(relative_paths), relative_paths
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
        - This is a convenience function that combines get_unstaged_changes() and stage_specific_files()
        - Stages both modified tracked files and untracked files
        - Returns True if no unstaged changes exist (no-op case)
        - Uses existing validation and error handling from underlying functions
        - Returns False if any files couldn't be staged
    """
    logger.debug("Staging all changes in %s", project_dir)

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return False

    try:
        # Get all unstaged changes
        unstaged_changes = get_unstaged_changes(project_dir)
        
        # Combine modified and untracked files
        all_unstaged_files = unstaged_changes["modified"] + unstaged_changes["untracked"]
        
        # If no unstaged changes, this is a successful no-op
        if not all_unstaged_files:
            logger.debug("No unstaged changes to stage - success")
            return True
        
        # Convert relative paths to absolute paths for stage_specific_files
        absolute_paths = []
        for file_path in all_unstaged_files:
            absolute_path = project_dir / file_path
            absolute_paths.append(absolute_path)
        
        # Stage all unstaged files using existing function
        logger.debug(
            "Staging %d unstaged files: %s", 
            len(absolute_paths), all_unstaged_files
        )
        
        result = stage_specific_files(absolute_paths, project_dir)
        
        if result:
            logger.info(
                "Successfully staged all %d unstaged changes", 
                len(absolute_paths)
            )
        else:
            logger.error("Failed to stage all unstaged changes")
        
        return result

    except Exception as e:
        logger.error("Unexpected error staging all changes: %s", e)
        return False
