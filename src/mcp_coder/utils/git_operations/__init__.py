"""Git operations package - modular git utilities."""

# Branch mutation operations
from .branches import (
    checkout_branch,
    create_branch,
    delete_branch,
)

# Commit operations
from .commits import commit_staged_files, get_latest_commit_sha

# Core types and utilities
from .core import CommitResult, PushResult

# Diff operations
from .diffs import get_branch_diff, get_git_diff_for_commit

# File tracking operations
from .file_tracking import git_move, is_file_tracked

# Repository status operations (from readers module)
# Branch reader operations (from readers module)
from .readers import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    get_parent_branch_name,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
    remote_branch_exists,
    validate_branch_name,
)

# Remote operations (including rebase_onto_branch)
from .remotes import (
    fetch_remote,
    get_github_repository_url,
    git_push,
    push_branch,
    rebase_onto_branch,
)

# Staging operations
from .staging import stage_all_changes, stage_specific_files

# Workflow orchestration
from .workflows import commit_all_changes

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
