"""Thin shim re-exporting GitHub operations.

Centralises all GitHub operation imports into a single module.
All symbols are re-exported from mcp_workspace.github_operations.
"""

from typing import List

# Top-level package exports
from mcp_workspace.github_operations import (
    BaseGitHubManager,
    CIResultsManager,
    CIStatusData,
    LabelData,
    LabelsManager,
    PullRequestManager,
    RepoIdentifier,
    get_authenticated_username,
)

# CI results submodule (TypedDicts + helpers)
from mcp_workspace.github_operations.ci_results_manager import (
    JobData,
    RunData,
    StepData,
    aggregate_conclusion,
    filter_runs_by_head_sha,
)

# GitHub utils submodule
from mcp_workspace.github_operations.github_utils import (
    format_github_https_url,
    get_repo_full_name,
    parse_github_url,
)

# Issues subpackage
from mcp_workspace.github_operations.issues import (
    BranchCreationResult,
    CacheData,
    CommentData,
    EventData,
    IssueBranchManager,
    IssueData,
    IssueEventType,
    IssueManager,
    _get_cache_file_path,
    _load_cache_file,
    _log_stale_cache_entries,
    _save_cache_file,
    create_empty_issue_data,
    generate_branch_name_from_issue,
    get_all_cached_issues,
    parse_base_branch,
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
    # CI results
    "CIResultsManager",
    "CIStatusData",
    "StepData",
    "JobData",
    "RunData",
    "filter_runs_by_head_sha",
    "aggregate_conclusion",
    # Labels
    "LabelData",
    "LabelsManager",
    # PR
    "PullRequestManager",
    "PullRequestData",
    # Repository
    "RepoIdentifier",
    "parse_github_url",
    "format_github_https_url",
    "get_repo_full_name",
    # Issues
    "IssueManager",
    "IssueBranchManager",
    "IssueEventType",
    "IssueData",
    "CommentData",
    "EventData",
    "BranchCreationResult",
    "CacheData",
    "create_empty_issue_data",
    "generate_branch_name_from_issue",
    "get_all_cached_issues",
    "update_issue_labels_in_cache",
    "parse_base_branch",
    # Cache internals (used by tests)
    "_get_cache_file_path",
    "_load_cache_file",
    "_save_cache_file",
    "_log_stale_cache_entries",
]
