"""GitHub operations module for MCP Coder.

This module provides GitHub API integration functionality for managing
pull requests, labels, and repository operations.
"""

from .base_manager import BaseGitHubManager
from .ci_results_manager import CIResultsManager, CIStatusData
from .github_utils import RepoIdentifier
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)
from .issue_cache import (
    CacheData,
    _update_issue_labels_in_cache,
    get_all_cached_issues,
)
from .issue_manager import CommentData, EventData, IssueData, IssueManager
from .labels_manager import LabelData, LabelsManager
from .pr_manager import PullRequestManager

__all__ = [
    "BaseGitHubManager",
    "BranchCreationResult",
    "CIResultsManager",
    "CIStatusData",
    "CacheData",
    "CommentData",
    "EventData",
    "IssueBranchManager",
    "IssueData",
    "IssueManager",
    "LabelData",
    "LabelsManager",
    "PullRequestManager",
    "RepoIdentifier",
    "_update_issue_labels_in_cache",
    "generate_branch_name_from_issue",
    "get_all_cached_issues",
]
