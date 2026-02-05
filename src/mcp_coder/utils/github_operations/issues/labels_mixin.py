"""Labels mixin for IssueManager.

This module provides the LabelsMixin class containing pure label operations
for managing issue labels through the GitHub API.
"""

import logging
from typing import TYPE_CHECKING, List

from mcp_coder.utils.log_utils import log_function_call

from ..base_manager import BaseGitHubManager, _handle_github_errors
from ..labels_manager import LabelData  # Per Decision #7
from .base import validate_issue_number
from .types import IssueData

if TYPE_CHECKING:
    pass  # Reserved for type-only imports if needed

logger = logging.getLogger(__name__)

__all__ = ["LabelsMixin"]


class LabelsMixin:
    """Mixin providing issue label operations.

    This mixin is designed to be used with BaseGitHubManager.
    Contains pure label operations only. Workflow orchestration
    (update_workflow_label) remains in IssueManager.
    """

    @log_function_call
    @_handle_github_errors(default_return=[])
    def get_available_labels(self: "BaseGitHubManager") -> List[LabelData]:
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

        # Get all labels from repository
        github_labels = repo.get_labels()

        # Convert to LabelData list
        labels: List[LabelData] = []
        for label in github_labels:
            labels.append(
                LabelData(
                    name=label.name,
                    color=label.color,
                    description=label.description or None,
                    url=label.url,
                )
            )

        return labels

    @log_function_call
    @_handle_github_errors(
        default_return=IssueData(
            number=0,
            title="",
            body="",
            state="",
            labels=[],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="",
            locked=False,
        )
    )
    def add_labels(
        self: "BaseGitHubManager", issue_number: int, *labels: str
    ) -> IssueData:
        """Add labels to an issue.

        Args:
            issue_number: Issue number to add labels to
            *labels: Variable number of label names to add

        Returns:
            IssueData with updated issue information, or empty IssueData on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> updated_issue = manager.add_labels(123, "bug", "high-priority")
            >>> print(f"Labels: {updated_issue['labels']}")
        """
        # Validate issue number
        if not validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                assignees=[],
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
                assignees=[],
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
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

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
            assignees=[assignee.login for assignee in github_issue.assignees],
            user=github_issue.user.login if github_issue.user else None,
            created_at=(
                github_issue.created_at.isoformat() if github_issue.created_at else None
            ),
            updated_at=(
                github_issue.updated_at.isoformat() if github_issue.updated_at else None
            ),
            url=github_issue.html_url,
            locked=github_issue.locked,
        )

    @log_function_call
    @_handle_github_errors(
        default_return=IssueData(
            number=0,
            title="",
            body="",
            state="",
            labels=[],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="",
            locked=False,
        )
    )
    def remove_labels(
        self: "BaseGitHubManager", issue_number: int, *labels: str
    ) -> IssueData:
        """Remove labels from an issue.

        Args:
            issue_number: Issue number to remove labels from
            *labels: Variable number of label names to remove

        Returns:
            IssueData with updated issue information, or empty IssueData on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> updated_issue = manager.remove_labels(123, "bug", "high-priority")
            >>> print(f"Labels: {updated_issue['labels']}")
        """
        # Validate issue number
        if not validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                assignees=[],
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
                assignees=[],
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
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

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
            assignees=[assignee.login for assignee in github_issue.assignees],
            user=github_issue.user.login if github_issue.user else None,
            created_at=(
                github_issue.created_at.isoformat() if github_issue.created_at else None
            ),
            updated_at=(
                github_issue.updated_at.isoformat() if github_issue.updated_at else None
            ),
            url=github_issue.html_url,
            locked=github_issue.locked,
        )

    @log_function_call
    @_handle_github_errors(
        default_return=IssueData(
            number=0,
            title="",
            body="",
            state="",
            labels=[],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="",
            locked=False,
        )
    )
    def set_labels(
        self: "BaseGitHubManager", issue_number: int, *labels: str
    ) -> IssueData:
        """Set labels on an issue, replacing all existing labels.

        Args:
            issue_number: Issue number to set labels on
            *labels: Variable number of label names to set (can be empty to remove all)

        Returns:
            IssueData with updated issue information, or empty IssueData on error

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
        if not validate_issue_number(issue_number):
            return IssueData(
                number=0,
                title="",
                body="",
                state="",
                labels=[],
                assignees=[],
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
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="",
                locked=False,
            )

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
            assignees=[assignee.login for assignee in github_issue.assignees],
            user=github_issue.user.login if github_issue.user else None,
            created_at=(
                github_issue.created_at.isoformat() if github_issue.created_at else None
            ),
            updated_at=(
                github_issue.updated_at.isoformat() if github_issue.updated_at else None
            ),
            url=github_issue.html_url,
            locked=github_issue.locked,
        )
