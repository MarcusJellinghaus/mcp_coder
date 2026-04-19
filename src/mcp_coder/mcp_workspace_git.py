"""Thin shim re-exporting git operations.

Centralises all git operation imports into a single module.
When mcp_workspace exposes git_operations submodules, change these
imports to point at mcp_workspace.file_tools.git_operations.*.
"""

# Branch queries
from mcp_coder.utils.git_operations.branch_queries import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    has_remote_tracking_branch,
    validate_branch_name,
)

# Branches
from mcp_coder.utils.git_operations.branches import (
    checkout_branch,
    create_branch,
    delete_branch,
)

# Commits
from mcp_coder.utils.git_operations.commits import (
    commit_staged_files,
    get_latest_commit_sha,
)

# Compact diffs
from mcp_coder.utils.git_operations.compact_diffs import get_compact_diff

# Core
from mcp_coder.utils.git_operations.core import CommitResult, _safe_repo_context

# Diffs
from mcp_coder.utils.git_operations.diffs import (
    get_branch_diff,
    get_git_diff_for_commit,
)

# Parent branch detection
from mcp_coder.utils.git_operations.parent_branch_detection import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
)

# Remotes
from mcp_coder.utils.git_operations.remotes import (
    fetch_remote,
    get_github_repository_url,
    git_push,
    push_branch,
    rebase_onto_branch,
)

# Repository status
from mcp_coder.utils.git_operations.repository_status import (
    get_full_status,
    is_git_repository,
    is_working_directory_clean,
)

# Staging
from mcp_coder.utils.git_operations.staging import stage_all_changes

# Workflows
from mcp_coder.utils.git_operations.workflows import commit_all_changes, needs_rebase

__all__ = [
    "CommitResult",
    "_safe_repo_context",
    "get_full_status",
    "is_git_repository",
    "is_working_directory_clean",
    "branch_exists",
    "extract_issue_number_from_branch",
    "get_current_branch_name",
    "get_default_branch_name",
    "has_remote_tracking_branch",
    "validate_branch_name",
    "checkout_branch",
    "create_branch",
    "delete_branch",
    "commit_staged_files",
    "get_latest_commit_sha",
    "get_branch_diff",
    "get_git_diff_for_commit",
    "get_compact_diff",
    "fetch_remote",
    "get_github_repository_url",
    "git_push",
    "push_branch",
    "rebase_onto_branch",
    "stage_all_changes",
    "commit_all_changes",
    "needs_rebase",
    "MERGE_BASE_DISTANCE_THRESHOLD",
    "detect_parent_branch_via_merge_base",
]
