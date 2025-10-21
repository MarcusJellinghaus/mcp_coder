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
    branch_exists,
    checkout_branch,
    commit_all_changes,
    commit_staged_files,
    create_branch,
    fetch_remote,
    get_branch_diff,
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    get_git_diff_for_commit,
    get_github_repository_url,
    get_parent_branch_name,
    get_staged_changes,
    get_unstaged_changes,
    git_move,
    git_push,
    is_file_tracked,
    is_git_repository,
    is_working_directory_clean,
    push_branch,
    stage_all_changes,
    stage_specific_files,
)

# GitHub operations
from .github_operations import PullRequestManager

# Jenkins operations
from .jenkins_operations import (
    JenkinsClient,
    JenkinsError,
    JobStatus,
    QueueSummary,
)
from .log_utils import log_function_call, setup_logging
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)
from .user_config import get_config_file_path, get_config_value

__all__ = [
    # Clipboard operations
    "get_clipboard_text",
    "parse_commit_message",
    "validate_commit_message",
    # Git operations
    "CommitResult",
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
    # GitHub operations
    "PullRequestManager",
    # Jenkins operations
    "JenkinsClient",
    "JenkinsError",
    "JobStatus",
    "QueueSummary",
]
