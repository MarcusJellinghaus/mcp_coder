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
    GitHubRateLimitError,
    LabelData,
    LabelsManager,
    PullRequestData,
    PullRequestManager,
    RepoIdentifier,
    get_authenticated_username,
    get_trusted_commenters,
    is_trusted_author,
    verify_github,
    verify_github_security,
)

# Caching: run-scoped issue → branch lookup cache
from mcp_workspace.github_operations.caching.branches import BranchLookupCache

# Caching: recognise rate-limit exceptions raised by managers
from mcp_workspace.github_operations.caching.errors import to_rate_limit_error

# Caching: run-scoped open-PR cache (caching/__init__.py is import-free)
from mcp_workspace.github_operations.caching.pull_requests import (
    OpenPullRequest,
    PullRequestCache,
)

# CI results submodule (TypedDicts + helpers)
from mcp_workspace.github_operations.ci_results_manager import (
    JobData,
)

# Issues subpackage
from mcp_workspace.github_operations.issues import (
    BranchLookup,
    BranchLookupError,
    CommentData,
    EventData,
    IssueBranchManager,
    IssueData,
    IssueEventType,
    IssueManager,
    create_empty_issue_data,
    get_all_cached_issues,
    get_issue_cache_last_checked,
    update_issue_labels_in_cache,
)
from mcp_workspace.github_operations.issues.linked_branches_mixin import ClosingPRRef

# PR submodule (TypedDicts)
from mcp_workspace.github_operations.pr_types import (
    ChangesRequestedData,
    ConversationCommentData,
    ReviewThreadData,
)

# Sourced from mcp_workspace.traffic_log (not github_operations): registers the
# command name written on every traffic-log line. Re-exported for the same reason
# as get_github_token.
from mcp_workspace.traffic_log import set_traffic_log_context

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
    # Rate limits
    "GitHubRateLimitError",
    "to_rate_limit_error",
    # Labels
    "LabelData",
    "LabelsManager",
    # PR
    "PullRequestManager",
    "PullRequestData",
    "PullRequestCache",
    "OpenPullRequest",
    "ChangesRequestedData",
    "ConversationCommentData",
    "ReviewThreadData",
    # Trust
    "get_trusted_commenters",
    "is_trusted_author",
    # Repository
    "RepoIdentifier",
    # Issues
    "IssueManager",
    "IssueBranchManager",
    "BranchLookup",
    "BranchLookupError",
    "BranchLookupCache",
    "ClosingPRRef",
    "IssueEventType",
    "IssueData",
    "CommentData",
    "EventData",
    "create_empty_issue_data",
    "get_all_cached_issues",
    "get_issue_cache_last_checked",
    "update_issue_labels_in_cache",
    # Token resolver (sourced from mcp_workspace.config)
    "get_github_token",
    # Traffic log context (sourced from mcp_workspace.traffic_log)
    "set_traffic_log_context",
]
