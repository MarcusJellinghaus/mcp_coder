"""GitHub operations module for MCP Coder.

This module provides GitHub API integration functionality for managing
pull requests, labels, and repository operations.
"""

from .base_manager import BaseGitHubManager
from .issue_manager import CommentData, IssueData, IssueManager, LabelData
from .labels_manager import LabelsManager
from .pr_manager import PullRequestManager

__all__ = [
    "BaseGitHubManager",
    "PullRequestManager",
    "LabelsManager",
    "IssueManager",
    "LabelData",
    "IssueData",
    "CommentData",
]
