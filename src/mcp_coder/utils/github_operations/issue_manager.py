"""Issue Manager for GitHub API operations.

This module provides data structures and the IssueManager class for managing
GitHub issues through the PyGithub library.
"""

import logging
from pathlib import Path
from typing import List, Optional, TypedDict

from github.GithubException import GithubException

from mcp_coder.utils.log_utils import log_function_call

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

    @log_function_call
    def create_issue(
        self, title: str, body: str = "", labels: Optional[List[str]] = None
    ) -> IssueData:
        """Create a new issue in the repository.

        Args:
            title: Issue title (required, cannot be empty)
            body: Issue description (optional)
            labels: List of label names to apply (optional)

        Returns:
            IssueData with created issue information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> issue = manager.create_issue(
            ...     title="Bug: Login fails",
            ...     body="Description of the bug",
            ...     labels=["bug", "high-priority"]
            ... )
            >>> print(f"Created issue #{issue['number']}")
        """
        # Validate title
        if not title or not title.strip():
            logger.error("Issue title cannot be empty")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        try:
            # Create issue
            github_issue = repo.create_issue(
                title=title.strip(), body=body, labels=labels or []
            )

            # Convert to IssueData
            return IssueData(
                number=github_issue.number,
                title=github_issue.title,
                body=github_issue.body or "",
                state=github_issue.state,
                labels=[label.name for label in github_issue.labels],
                user=github_issue.user.login if github_issue.user else None,
                created_at=(
                    github_issue.created_at.isoformat()
                    if github_issue.created_at
                    else None
                ),
                updated_at=(
                    github_issue.updated_at.isoformat()
                    if github_issue.updated_at
                    else None
                ),
                url=github_issue.html_url,
                locked=github_issue.locked,
            )

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(f"Authentication/permission error creating issue: {e}")
                raise
            # Log and return empty dict for other errors
            logger.error(f"Failed to create issue: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
        except Exception as e:
            logger.error(f"Unexpected error creating issue: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

    @log_function_call
    def close_issue(self, issue_number: int) -> IssueData:
        """Close an issue.

        Args:
            issue_number: Issue number to close

        Returns:
            IssueData with updated issue information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> closed_issue = manager.close_issue(123)
            >>> print(f"Issue state: {closed_issue['state']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        try:
            # Get and close issue
            github_issue = repo.get_issue(issue_number)
            github_issue.edit(state="closed")

            # Get fresh issue data after closing
            github_issue = repo.get_issue(issue_number)

            # Convert to IssueData
            return IssueData(
                number=github_issue.number,
                title=github_issue.title,
                body=github_issue.body or "",
                state=github_issue.state,
                labels=[label.name for label in github_issue.labels],
                user=github_issue.user.login if github_issue.user else None,
                created_at=(
                    github_issue.created_at.isoformat()
                    if github_issue.created_at
                    else None
                ),
                updated_at=(
                    github_issue.updated_at.isoformat()
                    if github_issue.updated_at
                    else None
                ),
                url=github_issue.html_url,
                locked=github_issue.locked,
            )

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(f"Authentication/permission error closing issue: {e}")
                raise
            # Log and return empty dict for other errors
            logger.error(f"Failed to close issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
        except Exception as e:
            logger.error(f"Unexpected error closing issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

    @log_function_call
    def reopen_issue(self, issue_number: int) -> IssueData:
        """Reopen a closed issue.

        Args:
            issue_number: Issue number to reopen

        Returns:
            IssueData with updated issue information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> reopened_issue = manager.reopen_issue(123)
            >>> print(f"Issue state: {reopened_issue['state']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        try:
            # Get and reopen issue
            github_issue = repo.get_issue(issue_number)
            github_issue.edit(state="open")

            # Get fresh issue data after reopening
            github_issue = repo.get_issue(issue_number)

            # Convert to IssueData
            return IssueData(
                number=github_issue.number,
                title=github_issue.title,
                body=github_issue.body or "",
                state=github_issue.state,
                labels=[label.name for label in github_issue.labels],
                user=github_issue.user.login if github_issue.user else None,
                created_at=(
                    github_issue.created_at.isoformat()
                    if github_issue.created_at
                    else None
                ),
                updated_at=(
                    github_issue.updated_at.isoformat()
                    if github_issue.updated_at
                    else None
                ),
                url=github_issue.html_url,
                locked=github_issue.locked,
            )

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(f"Authentication/permission error reopening issue: {e}")
                raise
            # Log and return empty dict for other errors
            logger.error(f"Failed to reopen issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
        except Exception as e:
            logger.error(f"Unexpected error reopening issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

    @log_function_call
    def get_available_labels(self) -> List[LabelData]:
        """Get all available labels in the repository.

        Returns:
            List of LabelData dictionaries with label information, or empty list on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> labels = manager.get_available_labels()
            >>> for label in labels:
            ...     print(f"{label['name']}: {label['color']}")
        """
        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return []

        try:
            # Get all labels from repository
            github_labels = repo.get_labels()

            # Convert to LabelData list
            labels: List[LabelData] = []
            for label in github_labels:
                labels.append(
                    LabelData(
                        name=label.name,
                        color=label.color,
                        description=label.description if label.description else None,
                    )
                )

            return labels

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(f"Authentication/permission error getting labels: {e}")
                raise
            # Log and return empty list for other errors
            logger.error(f"Failed to get repository labels: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting repository labels: {e}")
            return []

    @log_function_call
    def add_labels(self, issue_number: int, *labels: str) -> IssueData:
        """Add labels to an issue.

        Args:
            issue_number: Issue number to add labels to
            *labels: Variable number of label names to add

        Returns:
            IssueData with updated issue information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> updated_issue = manager.add_labels(123, "bug", "high-priority")
            >>> print(f"Labels: {updated_issue['labels']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Validate labels
        if not labels:
            logger.error("No labels provided")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        try:
            # Get issue and add labels
            github_issue = repo.get_issue(issue_number)
            github_issue.add_to_labels(*labels)

            # Get fresh issue data after adding labels
            github_issue = repo.get_issue(issue_number)

            # Convert to IssueData
            return IssueData(
                number=github_issue.number,
                title=github_issue.title,
                body=github_issue.body or "",
                state=github_issue.state,
                labels=[label.name for label in github_issue.labels],
                user=github_issue.user.login if github_issue.user else None,
                created_at=(
                    github_issue.created_at.isoformat()
                    if github_issue.created_at
                    else None
                ),
                updated_at=(
                    github_issue.updated_at.isoformat()
                    if github_issue.updated_at
                    else None
                ),
                url=github_issue.html_url,
                locked=github_issue.locked,
            )

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(
                    f"Authentication/permission error adding labels to issue: {e}"
                )
                raise
            # Log and return empty dict for other errors
            logger.error(f"Failed to add labels to issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
        except Exception as e:
            logger.error(f"Unexpected error adding labels to issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

    @log_function_call
    def remove_labels(self, issue_number: int, *labels: str) -> IssueData:
        """Remove labels from an issue.

        Args:
            issue_number: Issue number to remove labels from
            *labels: Variable number of label names to remove

        Returns:
            IssueData with updated issue information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> updated_issue = manager.remove_labels(123, "bug", "high-priority")
            >>> print(f"Labels: {updated_issue['labels']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Validate labels
        if not labels:
            logger.error("No labels provided")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        try:
            # Get issue and remove labels
            github_issue = repo.get_issue(issue_number)
            for label in labels:
                github_issue.remove_from_labels(label)

            # Get fresh issue data after removing labels
            github_issue = repo.get_issue(issue_number)

            # Convert to IssueData
            return IssueData(
                number=github_issue.number,
                title=github_issue.title,
                body=github_issue.body or "",
                state=github_issue.state,
                labels=[label.name for label in github_issue.labels],
                user=github_issue.user.login if github_issue.user else None,
                created_at=(
                    github_issue.created_at.isoformat()
                    if github_issue.created_at
                    else None
                ),
                updated_at=(
                    github_issue.updated_at.isoformat()
                    if github_issue.updated_at
                    else None
                ),
                url=github_issue.html_url,
                locked=github_issue.locked,
            )

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(
                    f"Authentication/permission error removing labels from issue: {e}"
                )
                raise
            # Log and return empty dict for other errors
            logger.error(f"Failed to remove labels from issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error removing labels from issue {issue_number}: {e}"
            )
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

    @log_function_call
    def set_labels(self, issue_number: int, *labels: str) -> IssueData:
        """Set labels on an issue, replacing all existing labels.

        Args:
            issue_number: Issue number to set labels on
            *labels: Variable number of label names to set (can be empty to remove all)

        Returns:
            IssueData with updated issue information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> updated_issue = manager.set_labels(123, "bug", "high-priority")
            >>> print(f"Labels: {updated_issue['labels']}")
            >>> # Remove all labels
            >>> updated_issue = manager.set_labels(123)
            >>> print(f"Labels: {updated_issue['labels']}")  # Empty list
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

        try:
            # Get issue and set labels (replaces all existing labels)
            github_issue = repo.get_issue(issue_number)
            github_issue.set_labels(*labels)

            # Get fresh issue data after setting labels
            github_issue = repo.get_issue(issue_number)

            # Convert to IssueData
            return IssueData(
                number=github_issue.number,
                title=github_issue.title,
                body=github_issue.body or "",
                state=github_issue.state,
                labels=[label.name for label in github_issue.labels],
                user=github_issue.user.login if github_issue.user else None,
                created_at=(
                    github_issue.created_at.isoformat()
                    if github_issue.created_at
                    else None
                ),
                updated_at=(
                    github_issue.updated_at.isoformat()
                    if github_issue.updated_at
                    else None
                ),
                url=github_issue.html_url,
                locked=github_issue.locked,
            )

        except GithubException as e:
            # Raise for auth/permission errors
            if e.status in (401, 403):
                logger.error(
                    f"Authentication/permission error setting labels on issue: {e}"
                )
                raise
            # Log and return empty dict for other errors
            logger.error(f"Failed to set labels on issue {issue_number}: {e}")
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error setting labels on issue {issue_number}: {e}"
            )
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )
