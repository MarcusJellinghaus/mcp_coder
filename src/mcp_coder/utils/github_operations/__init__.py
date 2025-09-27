"""GitHub operations module for MCP Coder.

This module provides GitHub API integration functionality for managing
pull requests and repository operations.
"""

from .pr_manager import PullRequestManager, create_pr_manager

__all__ = ["PullRequestManager", "create_pr_manager"]
