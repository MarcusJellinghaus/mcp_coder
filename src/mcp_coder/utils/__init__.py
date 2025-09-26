"""Utilities module for MCP Coder.

This module provides various utility functions including git operations,
subprocess execution, and other helper functions.
"""

from .clipboard import (
    get_clipboard_text,
    parse_commit_message,
    validate_commit_message,
)

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
from .log_utils import log_function_call, setup_logging
from .user_config import get_config_file_path, get_config_value
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)

__all__ = [
    # Clipboard operations
    "get_clipboard_text",
    "parse_commit_message",
    "validate_commit_message",
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
    # Logging utilities
    "log_function_call",
    "setup_logging",
    # User configuration
    "get_config_file_path",
    "get_config_value",
    # Subprocess operations
    "CommandOptions",
    "CommandResult",
    "execute_command",
    "execute_subprocess",
]
