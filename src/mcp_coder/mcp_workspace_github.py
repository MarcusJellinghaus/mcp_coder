"""Thin shim re-exporting GitHub operations.

Centralises all GitHub operation imports into a single module.
All symbols are re-exported from mcp_workspace.github_operations.
"""

from typing import List

# Top-level package exports
from mcp_workspace.github_operations import (
    BaseGitHubManager,
    CheckResult,
    CIResultsManager,
    CIStatusData,
    LabelData,
    LabelsManager,
    PullRequestManager,
    RepoIdentifier,
    get_authenticated_username,
    verify_github,
)

# CI results submodule (TypedDicts + helpers)
from mcp_workspace.github_operations.ci_results_manager import (
    JobData,
)

# Issues subpackage
from mcp_workspace.github_operations.issues import (
    CacheData,
    CommentData,
    IssueBranchManager,
    IssueData,
    IssueEventType,
    IssueManager,
)
from mcp_workspace.github_operations.issues import (
    _get_cache_file_path as get_cache_file_path,
)
from mcp_workspace.github_operations.issues import _load_cache_file as load_cache_file
from mcp_workspace.github_operations.issues import (
    _log_stale_cache_entries as log_stale_cache_entries,
)
from mcp_workspace.github_operations.issues import _save_cache_file as save_cache_file
from mcp_workspace.github_operations.issues import (
    get_all_cached_issues,
    update_issue_labels_in_cache,
)

# PR submodule (PullRequestData TypedDict)
from mcp_workspace.github_operations.pr_manager import (
    PullRequestData,
)

__all__: List[str] = [
    # Base manager
    "BaseGitHubManager",
    "get_authenticated_username",
    # Verification
    "CheckResult",
    "verify_github",
    # CI results
    "CIResultsManager",
    "CIStatusData",
    "JobData",
    # Labels
    "LabelData",
    "LabelsManager",
    # PR
    "PullRequestManager",
    "PullRequestData",
    # Repository
    "RepoIdentifier",
    # Issues
    "IssueManager",
    "IssueBranchManager",
    "IssueEventType",
    "IssueData",
    "CommentData",
    "CacheData",
    "get_all_cached_issues",
    "update_issue_labels_in_cache",
    # Cache helpers (public re-exports drop the underscore)
    "get_cache_file_path",
    "load_cache_file",
    "save_cache_file",
    "log_stale_cache_entries",
]
