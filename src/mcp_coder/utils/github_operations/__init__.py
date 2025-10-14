"""GitHub operations module for MCP Coder.

This module provides GitHub API integration functionality for managing
pull requests, labels, and repository operations.
"""

from .base_manager import BaseGitHubManager
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)
from .issue_manager import CommentData, EventData, IssueData, IssueManager
from .labels_manager import LabelData, LabelsManager
from .pr_manager import PullRequestManager

__all__ = [
    "BaseGitHubManager",
    "BranchCreationResult",
    "CommentData",
    "EventData",
    "IssueBranchManager",
    "IssueData",
    "IssueManager",
    "LabelData",
    "LabelsManager",
    "PullRequestManager",
    "generate_branch_name_from_issue",
]
