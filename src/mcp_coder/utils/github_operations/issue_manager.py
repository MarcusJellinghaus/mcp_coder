"""Issue Manager for GitHub API operations.

This module provides data structures and the IssueManager class for managing
GitHub issues through the PyGithub library.
"""

import logging
from pathlib import Path
from typing import List, Optional, TypedDict

from .base_manager import BaseGitHubManager

# Configure logger for GitHub operations
logger = logging.getLogger(__name__)


class IssueData(TypedDict):
    """TypedDict for issue data structure.

    Represents a GitHub issue with all relevant fields returned from the GitHub API.
    """

    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    user: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    url: str
    locked: bool


class CommentData(TypedDict):
    """TypedDict for issue comment data structure.

    Represents a comment on a GitHub issue with all relevant fields.
    """

    id: int
    body: str
    user: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    url: str


class LabelData(TypedDict):
    """TypedDict for label data structure.

    Represents a GitHub repository label with all relevant fields.
    """

    name: str
    color: str
    description: Optional[str]


class IssueManager(BaseGitHubManager):
    """Manages GitHub issue operations using the GitHub API.

    This class provides methods for creating, retrieving, listing, and managing
    GitHub issues and their comments in a repository.

    Configuration:
        Requires GitHub token in config file (~/.mcp_coder/config.toml):

        [github]
        token = "ghp_your_personal_access_token_here"

        Token needs 'repo' scope for private repositories, 'public_repo' for public.
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        """Initialize the IssueManager.

        Args:
            project_dir: Path to the project directory containing git repository

        Raises:
            ValueError: If project_dir is None, directory doesn't exist,
                       is not a git repository, or GitHub token is not configured
        """
        super().__init__(project_dir)

    def _validate_issue_number(self, issue_number: int) -> bool:
        """Validate issue number.

        Args:
            issue_number: Issue number to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(issue_number, int) or issue_number <= 0:
            logger.error(
                f"Invalid issue number: {issue_number}. Must be a positive integer."
            )
            return False
        return True

    def _validate_comment_id(self, comment_id: int) -> bool:
        """Validate comment ID.

        Args:
            comment_id: Comment ID to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(comment_id, int) or comment_id <= 0:
            logger.error(
                f"Invalid comment ID: {comment_id}. Must be a positive integer."
            )
            return False
        return True
