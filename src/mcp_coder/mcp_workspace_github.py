"""Thin shim re-exporting GitHub operations.

Centralises all GitHub operation imports into a single module.
All symbols are re-exported from mcp_workspace.github_operations.

When mcp_workspace.github_operations is not yet installed, the module
still imports successfully but every exported name is replaced by a
lazy-error sentinel that raises ``ImportError`` on first use.
"""

from typing import Any, List

_AVAILABLE = True

try:
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

except ImportError:
    _AVAILABLE = False

    class _MissingSentinel:
        """Placeholder that raises ImportError on any use."""

        def __init__(self, name: str) -> None:
            self._name = name

        def _error(self) -> ImportError:
            return ImportError(
                f"Cannot use '{self._name}': mcp_workspace.github_operations "
                "is not installed. Install a version of mcp-workspace that "
                "includes the github_operations submodule."
            )

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            raise self._error()

        def __getattr__(self, item: str) -> Any:
            # Allow Python's typing machinery to probe for dunder attributes
            # (e.g. __typing_subst__) without raising ImportError.
            if item.startswith("__") and item.endswith("__"):
                raise AttributeError(item)
            raise self._error()

        def __instancecheck__(self, instance: Any) -> bool:
            raise self._error()

        def __repr__(self) -> str:
            return f"<missing: {self._name}>"

    # Create sentinels for every exported name so that
    # `from mcp_coder.mcp_workspace_github import X` succeeds at import time.
    # Sentinels raise ImportError with a helpful message on first real use.
    BaseGitHubManager = _MissingSentinel("BaseGitHubManager")  # type: ignore[assignment,misc]
    CIResultsManager = _MissingSentinel("CIResultsManager")  # type: ignore[assignment,misc]
    CIStatusData = _MissingSentinel("CIStatusData")  # type: ignore[assignment,misc]
    LabelData = _MissingSentinel("LabelData")  # type: ignore[assignment,misc]
    LabelsManager = _MissingSentinel("LabelsManager")  # type: ignore[assignment,misc]
    PullRequestManager = _MissingSentinel("PullRequestManager")  # type: ignore[assignment,misc]
    RepoIdentifier = _MissingSentinel("RepoIdentifier")  # type: ignore[assignment,misc]
    get_authenticated_username = _MissingSentinel("get_authenticated_username")  # type: ignore[assignment,misc]
    JobData = _MissingSentinel("JobData")  # type: ignore[assignment,misc]
    RunData = _MissingSentinel("RunData")  # type: ignore[assignment,misc]
    StepData = _MissingSentinel("StepData")  # type: ignore[assignment,misc]
    aggregate_conclusion = _MissingSentinel("aggregate_conclusion")  # type: ignore[assignment,misc]
    filter_runs_by_head_sha = _MissingSentinel("filter_runs_by_head_sha")  # type: ignore[assignment,misc]
    format_github_https_url = _MissingSentinel("format_github_https_url")  # type: ignore[assignment,misc]
    get_repo_full_name = _MissingSentinel("get_repo_full_name")  # type: ignore[assignment,misc]
    parse_github_url = _MissingSentinel("parse_github_url")  # type: ignore[assignment,misc]
    BranchCreationResult = _MissingSentinel("BranchCreationResult")  # type: ignore[assignment,misc]
    CacheData = _MissingSentinel("CacheData")  # type: ignore[assignment,misc]
    CommentData = _MissingSentinel("CommentData")  # type: ignore[assignment,misc]
    EventData = _MissingSentinel("EventData")  # type: ignore[assignment,misc]
    IssueBranchManager = _MissingSentinel("IssueBranchManager")  # type: ignore[assignment,misc]
    IssueData = _MissingSentinel("IssueData")  # type: ignore[assignment,misc]
    IssueEventType = _MissingSentinel("IssueEventType")  # type: ignore[assignment,misc]
    IssueManager = _MissingSentinel("IssueManager")  # type: ignore[assignment,misc]
    _get_cache_file_path = _MissingSentinel("_get_cache_file_path")  # type: ignore[assignment,misc]
    _load_cache_file = _MissingSentinel("_load_cache_file")  # type: ignore[assignment,misc]
    _log_stale_cache_entries = _MissingSentinel("_log_stale_cache_entries")  # type: ignore[assignment,misc]
    _save_cache_file = _MissingSentinel("_save_cache_file")  # type: ignore[assignment,misc]
    create_empty_issue_data = _MissingSentinel("create_empty_issue_data")  # type: ignore[assignment,misc]
    generate_branch_name_from_issue = _MissingSentinel("generate_branch_name_from_issue")  # type: ignore[assignment,misc]
    get_all_cached_issues = _MissingSentinel("get_all_cached_issues")  # type: ignore[assignment,misc]
    parse_base_branch = _MissingSentinel("parse_base_branch")  # type: ignore[assignment,misc]
    update_issue_labels_in_cache = _MissingSentinel("update_issue_labels_in_cache")  # type: ignore[assignment,misc]
    PullRequestData = _MissingSentinel("PullRequestData")  # type: ignore[assignment,misc]

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
