"""Utilities module for MCP Coder.

This module provides various utility functions including git operations,
subprocess execution, and other helper functions.
"""

# Import all git operations for easy access
from .git_operations import (
    CommitResult,
    commit_all_changes,
    commit_staged_files,
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    git_move,
    is_file_tracked,
    is_git_repository,
    stage_all_changes,
    stage_specific_files,
)
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)

__all__ = [
    # Git operations
    "CommitResult",
    "commit_all_changes",
    "commit_staged_files",
    "get_full_status",
    "get_staged_changes",
    "get_unstaged_changes",
    "git_move",
    "is_file_tracked",
    "is_git_repository",
    "stage_all_changes",
    "stage_specific_files",
    # Subprocess operations
    "CommandOptions",
    "CommandResult",
    "execute_command",
    "execute_subprocess",
]
