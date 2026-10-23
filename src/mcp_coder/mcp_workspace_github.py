"""Thin shim re-exporting GitHub operations.

Centralises all GitHub operation imports into a single module.
All symbols are re-exported from mcp_workspace.github_operations.
"""

# Sourced from mcp_workspace.config (not github_operations): GitHub token resolver
# (env var → config file → None). Re-exported here so callers obey the CLAUDE.md rule
# against importing mcp_workspace.* directly.
from mcp_workspace.config import get_github_token

# Top-level package exports
from mcp_workspace.github_operations import (
    BaseGitHubManager,
    CheckResult,
    CIResultsManager,
    CIStatusData,
    GithubException,
    LabelData,
    LabelsManager,
    PullRequestData,
    PullRequestManager,
    RepoIdentifier,
    get_authenticated_username,
    verify_github,
    verify_github_security,
)

# CI results submodule (TypedDicts + helpers)
from mcp_workspace.github_operations.ci_results_manager import (
    JobData,
)

# Issues subpackage
from mcp_workspace.github_operations.issues import (
    CacheData,
    CommentData,
    EventData,
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
    create_empty_issue_data,
    get_all_cached_issues,
    update_issue_labels_in_cache,
)
from mcp_workspace.github_operations.issues.linked_branches_mixin import ClosingPRRef

# PR submodule (TypedDicts)
from mcp_workspace.github_operations.pr_types import (
    ChangesRequestedData,
    ConversationCommentData,
)

__all__: list[str] = [
    # Base manager
    "BaseGitHubManager",
    "get_authenticated_username",
    # Verification
    "CheckResult",
    "verify_github",
    "verify_github_security",
    # CI results
    "CIResultsManager",
    "CIStatusData",
    "JobData",
    # Re-exported so ci.py can classify raised exceptions without a direct
    # `github` import, which the github_library_isolation contract forbids.
    "GithubException",
    # Labels
    "LabelData",
    "LabelsManager",
    # PR
    "PullRequestManager",
    "PullRequestData",
    "ChangesRequestedData",
    "ConversationCommentData",
    # Repository
    "RepoIdentifier",
    # Issues
    "IssueManager",
    "IssueBranchManager",
    "ClosingPRRef",
    "IssueEventType",
    "IssueData",
    "CommentData",
    "CacheData",
    "EventData",
    "create_empty_issue_data",
    "get_all_cached_issues",
    "update_issue_labels_in_cache",
    # Cache helpers (public re-exports drop the underscore)
    "get_cache_file_path",
    "load_cache_file",
    "save_cache_file",
    "log_stale_cache_entries",
    # Token resolver (sourced from mcp_workspace.config)
    "get_github_token",
]
