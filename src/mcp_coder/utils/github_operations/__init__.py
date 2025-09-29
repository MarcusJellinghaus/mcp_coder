"""GitHub operations module for MCP Coder.

This module provides GitHub API integration functionality for managing
pull requests, labels, and repository operations.
"""

from .base_manager import BaseGitHubManager
from .labels_manager import LabelData, LabelsManager
from .pr_manager import PullRequestManager

__all__ = [
    "BaseGitHubManager",
    "PullRequestManager",
    "LabelsManager",
    "LabelData",
]
