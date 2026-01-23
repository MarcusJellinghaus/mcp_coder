"""Git operations package - modular git utilities."""

# Branch operations
from .branches import (
    branch_exists,
    checkout_branch,
    create_branch,
    delete_branch,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_parent_branch_name,
    rebase_onto_branch,
    remote_branch_exists,
    validate_branch_name,
)

# Commit operations
from .commits import commit_all_changes, commit_staged_files, get_latest_commit_sha

# Core types and utilities
from .core import CommitResult, PushResult

# Diff operations
from .diffs import get_branch_diff, get_git_diff_for_commit

# File tracking operations
from .file_tracking import git_move, is_file_tracked

# Remote operations
from .remotes import fetch_remote, get_github_repository_url, git_push, push_branch

# Repository operations
from .repository import (
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
)

# Staging operations
from .staging import stage_all_changes, stage_specific_files

__all__ = [
    # Types
    "CommitResult",
    "PushResult",
    # Branch operations
    "branch_exists",
    "checkout_branch",
    "create_branch",
    "delete_branch",
    "extract_issue_number_from_branch",
    "get_current_branch_name",
    "get_default_branch_name",
    "get_parent_branch_name",
    "rebase_onto_branch",
    "remote_branch_exists",
    "validate_branch_name",
    # Commit operations
    "commit_all_changes",
    "commit_staged_files",
    "get_latest_commit_sha",
    # Diff operations
    "get_branch_diff",
    "get_git_diff_for_commit",
    # File tracking
    "git_move",
    "is_file_tracked",
    # Remote operations
    "fetch_remote",
    "get_github_repository_url",
    "git_push",
    "push_branch",
    # Repository operations
    "get_full_status",
    "get_staged_changes",
    "get_unstaged_changes",
    "is_git_repository",
    "is_working_directory_clean",
    # Staging operations
    "stage_all_changes",
    "stage_specific_files",
]
