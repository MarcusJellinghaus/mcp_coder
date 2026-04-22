"""Thin shim re-exporting git operations from mcp_workspace.

Centralises all git operation imports into a single module.
All mcp_coder code must import git operations through this shim.

Git functionality lives in the mcp_workspace package.
File issues or feature requests there: MarcusJellinghaus/mcp-workspace
"""

# Branch queries
from mcp_workspace.git_operations.branch_queries import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    has_remote_tracking_branch,
    validate_branch_name,
)

# Branches
from mcp_workspace.git_operations.branches import (
    checkout_branch,
    create_branch,
    delete_branch,
)

# Commits
from mcp_workspace.git_operations.commits import (
    commit_staged_files,
    get_latest_commit_sha,
)

# Compact diffs
from mcp_workspace.git_operations.compact_diffs import get_compact_diff

# Core
from mcp_workspace.git_operations.core import CommitResult

# Diffs
from mcp_workspace.git_operations.diffs import (
    get_branch_diff,
    get_git_diff_for_commit,
)

# Parent branch detection
from mcp_workspace.git_operations.parent_branch_detection import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
)

# Remotes
from mcp_workspace.git_operations.remotes import (
    fetch_remote,
    get_github_repository_url,
    git_push,
    push_branch,
    rebase_onto_branch,
)

# Repository status
from mcp_workspace.git_operations.repository_status import (
    get_full_status,
    is_git_repository,
    is_working_directory_clean,
)

# Staging
from mcp_workspace.git_operations.staging import stage_all_changes

# Workflows
from mcp_workspace.git_operations.workflows import commit_all_changes, needs_rebase

__all__ = [
    "CommitResult",
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
