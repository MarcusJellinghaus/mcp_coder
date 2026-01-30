"""Issue Manager for GitHub API operations.

This module provides data structures and the IssueManager class for managing
GitHub issues through the PyGithub library.
"""

import logging
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, NotRequired, Optional, TypedDict

from github.GithubException import GithubException

from mcp_coder.utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
from mcp_coder.utils.github_operations.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.log_utils import log_function_call

from .base_manager import BaseGitHubManager, _handle_github_errors

# Configure logger for GitHub operations
logger = logging.getLogger(__name__)

# Export public API
__all__ = [
    "IssueEventType",
    "IssueData",
    "CommentData",
    "LabelData",
    "EventData",
    "IssueManager",
]


class IssueEventType(str, Enum):
    """Enum for GitHub issue event types."""

    # Label events
    LABELED = "labeled"
    UNLABELED = "unlabeled"

    # State events
    CLOSED = "closed"
    REOPENED = "reopened"

    # Assignment events
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"

    # Milestone events
    MILESTONED = "milestoned"
    DEMILESTONED = "demilestoned"

    # Reference events
    REFERENCED = "referenced"
    CROSS_REFERENCED = "cross-referenced"

    # Interaction events
    COMMENTED = "commented"
    MENTIONED = "mentioned"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"

    # Title/Lock events
    RENAMED = "renamed"
    LOCKED = "locked"
    UNLOCKED = "unlocked"

    # PR-specific events (included for completeness)
    REVIEW_REQUESTED = "review_requested"
    REVIEW_REQUEST_REMOVED = "review_request_removed"
    CONVERTED_TO_DRAFT = "converted_to_draft"
    READY_FOR_REVIEW = "ready_for_review"


class IssueData(TypedDict):
    """TypedDict for issue data structure.

    Represents a GitHub issue with all relevant fields returned from the GitHub API.
    """

    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]
    user: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    url: str
    locked: bool
    base_branch: NotRequired[Optional[str]]


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


class EventData(TypedDict):
    """TypedDict for issue event data structure."""

    event: str  # Event type (e.g., "labeled", "unlabeled")
    label: Optional[str]  # Label name (for label events)
    created_at: str  # ISO format timestamp
    actor: Optional[str]  # GitHub username who performed action


def _parse_base_branch(body: str) -> Optional[str]:
    """Parse base branch from issue body.

    Looks for a markdown heading (any level) containing "Base Branch" (case-insensitive)
    and extracts the content until the next heading.

    Args:
        body: GitHub issue body text

    Returns:
        Branch name if found and valid, None if not specified or empty

    Raises:
        ValueError: If base branch section contains multiple lines (malformed input)

    Example:
        >>> _parse_base_branch("### Base Branch\\n\\nfeature/v2\\n\\n### Description")
        'feature/v2'
        >>> _parse_base_branch("### Description\\n\\nNo base branch")
        None
    """
    if not body:
        return None

    # Case-insensitive match for any heading level (# to ######) with "Base Branch"
    # MULTILINE flag for ^ to match line starts, DOTALL for . to match newlines
    pattern = r"(?im)^#{1,6}\s*base\s*branch\s*\n(.*?)(?=^#{1,6}\s|\Z)"
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL)

    if not match:
        return None

    content = match.group(1).strip()

    if not content:
        return None

    # Check for multi-line content (malformed input)
    if "\n" in content:
        raise ValueError(
            f"Base branch section contains multiple lines (malformed): {content!r}"
        )

    return content


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

    def __init__(
        self, project_dir: Optional[Path] = None, repo_url: Optional[str] = None
    ) -> None:
        """Initialize the IssueManager.

        Args:
            project_dir: Path to the project directory containing git repository
            repo_url: GitHub repository URL (e.g., "https://github.com/user/repo.git")

        Raises:
            ValueError: If neither or both parameters provided, directory doesn't exist,
                       is not a git repository, or GitHub token is not configured
        """
        super().__init__(project_dir=project_dir, repo_url=repo_url)

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
    def create_issue(
        self, title: str, body: str = "", labels: Optional[List[str]] = None
    ) -> IssueData:
        """Create a new issue in the repository.

        Args:
            title: Issue title (required, cannot be empty)
            body: Issue description (optional)
            labels: List of label names to apply (optional)

        Returns:
            IssueData with created issue information, or empty IssueData on error

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
    def update_workflow_label(
        self,
        from_label_id: str,
        to_label_id: str,
        branch_name: Optional[str] = None,
        validated_issue_number: Optional[int] = None,
    ) -> bool:
        """Update workflow label after successful workflow completion.

        This method handles complete label transition workflow:
        1. Extract issue number from branch name (or detect current branch)
        2. Verify branch is linked to the issue via GitHub API
        3. Look up actual label names from internal IDs
        4. Perform label transition (remove old, add new)

        Non-blocking: All errors are caught, logged, and return False.
        Workflow success is never affected by label update failures.

        Args:
            from_label_id: Internal ID of source label (e.g., "implementing")
            to_label_id: Internal ID of target label (e.g., "code_review")
            branch_name: Optional branch name. If None, detects current branch.
            validated_issue_number: Optional pre-validated issue number. If provided,
                skips branch detection and linkage validation. Use this when the
                branch-issue linkage has been verified earlier in the workflow
                (e.g., before PR creation when GitHub removes the linkage).

        Returns:
            True if label updated successfully, False otherwise

        Example:
            >>> manager = IssueManager(project_dir)
            >>> success = manager.update_workflow_label("implementing", "code_review")
            >>> if success:
            ...     print("Label updated")
        """
        try:
            # Check for pre-validated issue number
            if validated_issue_number is not None:
                issue_number = validated_issue_number
                # Skip to step 4 (label config loading)
            else:
                # Step 1: Get branch name (provided or auto-detect)
                actual_branch_name: str
                if branch_name is None:
                    # project_dir can be None if initialized with repo_url
                    if self.project_dir is None:
                        logger.error(
                            "Cannot auto-detect branch name without project_dir. "
                            "Please provide branch_name parameter."
                        )
                        return False
                    detected_branch = get_current_branch_name(self.project_dir)
                    if detected_branch is None:
                        logger.error(
                            "Failed to detect current branch name. "
                            "Please provide branch_name parameter."
                        )
                        return False
                    actual_branch_name = detected_branch
                else:
                    actual_branch_name = branch_name

                # Step 2: Extract issue number from branch name
                extracted_issue_number = extract_issue_number_from_branch(
                    actual_branch_name
                )
                if extracted_issue_number is None:
                    logger.warning(
                        f"Branch '{actual_branch_name}' does not follow {{issue_number}}-title pattern"
                    )
                    return False
                issue_number = extracted_issue_number

                # Step 3: Verify branch is linked to the issue
                # Construct repo_url from _repo_full_name if available, otherwise use project_dir
                repo_url = None
                if self._repo_full_name is not None:
                    repo_url = f"https://github.com/{self._repo_full_name}.git"

                branch_manager = IssueBranchManager(
                    project_dir=self.project_dir, repo_url=repo_url
                )
                linked_branches = branch_manager.get_linked_branches(issue_number)

                if actual_branch_name not in linked_branches:
                    logger.warning(
                        f"Branch '{actual_branch_name}' is not linked to issue #{issue_number}. "
                        f"Linked branches: {linked_branches}"
                    )
                    return False

            # Step 4: Load label config and build lookups
            # project_dir is required for label config
            if self.project_dir is None:
                logger.error(
                    "Cannot load label config without project_dir. "
                    "Label update is not supported for repo_url mode."
                )
                return False

            config_path = get_labels_config_path(self.project_dir)
            label_config = load_labels_config(config_path)
            label_lookups = build_label_lookups(label_config)

            # Step 5: Lookup actual label names from internal IDs
            from_label_name = label_lookups["id_to_name"].get(from_label_id)
            to_label_name = label_lookups["id_to_name"].get(to_label_id)

            if not from_label_name:
                logger.error(
                    f"Label ID '{from_label_id}' not found in configuration. "
                    f"Available IDs: {list(label_lookups['id_to_name'].keys())}"
                )
                return False

            if not to_label_name:
                logger.error(
                    f"Label ID '{to_label_id}' not found in configuration. "
                    f"Available IDs: {list(label_lookups['id_to_name'].keys())}"
                )
                return False

            # Step 6: Get current issue labels
            issue_data = self.get_issue(issue_number)
            if issue_data["number"] == 0:
                logger.error(f"Failed to get issue #{issue_number}")
                return False

            current_labels = set(issue_data["labels"])

            # Step 7: Check if already in target state (idempotent)
            if to_label_name in current_labels:
                if from_label_name not in current_labels:
                    # Already transitioned, nothing to do
                    logger.debug(
                        f"Issue #{issue_number} already has label '{to_label_name}' "
                        f"without '{from_label_name}'. No action needed."
                    )
                    return True
                # else: Has both labels, proceed with removal of old label

            # Log if source label is not present (but target label is also not present)
            if from_label_name not in current_labels:
                logger.info(
                    f"Source label '{from_label_name}' not present on issue #{issue_number}. "
                    "Proceeding with transition."
                )

            # Step 8: Compute new label set
            new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}

            # Step 9: Apply label transition
            result = self.set_labels(issue_number, *new_labels)
            if result["number"] == 0:
                logger.error(f"Failed to update labels for issue #{issue_number}")
                return False

            logger.info(
                f"Successfully updated issue #{issue_number} label: "
                f"{from_label_name} → {to_label_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Unexpected error updating workflow label: {e}")
            return False

    @log_function_call
    def get_issue_events(
        self, issue_number: int, filter_by_type: Optional[IssueEventType] = None
    ) -> List[EventData]:
        """Get timeline events for an issue.

        Args:
            issue_number: Issue number to get events for
            filter_by_type: Optional event type to filter by (e.g., IssueEventType.LABELED)
                           If None, returns all event types

        Returns:
            List of EventData dicts with event information

        Raises:
            GithubException: For authentication, permission, or API errors

        Note:
            Returns ALL event types by default. Currently, the validation workflow
            only uses label events (labeled/unlabeled), but other event types are
            available for future use.

        Example:
            >>> # Get all events
            >>> events = manager.get_issue_events(123)
            >>> # Get only labeled events
            >>> labeled = manager.get_issue_events(123, IssueEventType.LABELED)
            >>> for event in labeled:
            ...     print(f"Label '{event['label']}' added at {event['created_at']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return []

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return []

        # Get issue
        try:
            github_issue = repo.get_issue(issue_number)
        except GithubException as e:
            logger.error(f"Failed to get issue #{issue_number}: {e}")
            raise

        # Get events
        try:
            github_events = github_issue.get_events()
        except GithubException as e:
            logger.error(f"Failed to get events for issue #{issue_number}: {e}")
            raise

        # Convert to EventData list
        events: List[EventData] = []
        for event in github_events:
            # Skip if filter_by_type is provided and doesn't match
            if filter_by_type is not None and event.event != filter_by_type.value:
                continue

            # Extract label name for labeled/unlabeled events
            label_name = None
            if event.event in ["labeled", "unlabeled"] and hasattr(event, "label"):
                label_name = event.label.name if event.label else None

            # Extract actor username
            actor_username = None
            if hasattr(event, "actor") and event.actor:
                actor_username = event.actor.login

            # Format timestamp to ISO string
            created_at = event.created_at.isoformat() if event.created_at else ""

            # Create EventData
            events.append(
                EventData(
                    event=event.event,
                    label=label_name,
                    created_at=created_at,
                    actor=actor_username,
                )
            )

        return events

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
    def get_issue(self, issue_number: int) -> IssueData:
        """Retrieve issue details by number.

        Args:
            issue_number: Issue number to retrieve

        Returns:
            IssueData with issue information, or empty IssueData on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> issue = manager.get_issue(123)
            >>> print(f"Issue: {issue['title']}")
            >>> print(f"Assignees: {issue['assignees']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
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

        # Get issue
        github_issue = repo.get_issue(issue_number)

        # Parse base_branch from body
        body = github_issue.body or ""
        try:
            base_branch = _parse_base_branch(body)
        except ValueError as e:
            logger.warning(f"Issue #{issue_number} has malformed base branch: {e}")
            base_branch = None

        # Convert to IssueData
        return IssueData(
            number=github_issue.number,
            title=github_issue.title,
            body=body,
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
            base_branch=base_branch,
        )

    @log_function_call
    @_handle_github_errors(default_return=[])
    def list_issues(
        self,
        state: str = "open",
        include_pull_requests: bool = False,
        since: Optional[datetime] = None,
    ) -> List[IssueData]:
        """List all issues in the repository with pagination support.

        Args:
            state: Issue state filter - 'open', 'closed', or 'all' (default: 'open')
            include_pull_requests: Whether to include PRs in results (default: False)
            since: Only fetch issues updated after this time (optional)

        Returns:
            List of IssueData dictionaries with issue information, or empty list on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> issues = manager.list_issues(state='open', include_pull_requests=False)
            >>> print(f"Found {len(issues)} open issues")
            >>> for issue in issues:
            ...     print(f"#{issue['number']}: {issue['title']}")
            >>> # Get issues updated since a specific time
            >>> from datetime import datetime
            >>> cutoff_time = datetime(2023, 1, 1)
            >>> recent_issues = manager.list_issues(since=cutoff_time)
        """
        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return []

        # Get issues with pagination support (PyGithub handles this automatically)
        # Pass since parameter to PyGithub's get_issues() when provided
        issues_list: List[IssueData] = []
        if since is not None:
            issues_iterator = repo.get_issues(state=state, since=since)
        else:
            issues_iterator = repo.get_issues(state=state)

        for issue in issues_iterator:
            # Filter out pull requests if not requested
            if not include_pull_requests and issue.pull_request is not None:
                continue

            # Parse base_branch from body
            body = issue.body or ""
            try:
                base_branch = _parse_base_branch(body)
            except ValueError as e:
                logger.warning(f"Issue #{issue.number} has malformed base branch: {e}")
                base_branch = None

            # Convert to IssueData
            issue_data = IssueData(
                number=issue.number,
                title=issue.title,
                body=body,
                state=issue.state,
                labels=[label.name for label in issue.labels],
                assignees=[assignee.login for assignee in issue.assignees],
                user=issue.user.login if issue.user else None,
                created_at=(issue.created_at.isoformat() if issue.created_at else None),
                updated_at=(issue.updated_at.isoformat() if issue.updated_at else None),
                url=issue.html_url,
                locked=issue.locked,
                base_branch=base_branch,
            )
            issues_list.append(issue_data)

        return issues_list

    @log_function_call
    @_handle_github_errors(
        default_return=CommentData(
            id=0,
            body="",
            user=None,
            created_at=None,
            updated_at=None,
            url="",
        )
    )
    def add_comment(self, issue_number: int, body: str) -> CommentData:
        """Add a comment to an issue.

        Args:
            issue_number: Issue number to add comment to
            body: Comment text (required, cannot be empty)

        Returns:
            CommentData with created comment information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> comment = manager.add_comment(123, "This is a test comment")
            >>> print(f"Created comment {comment['id']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Validate body
        if not body or not body.strip():
            logger.error("Comment body cannot be empty")
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Get issue and create comment
        github_issue = repo.get_issue(issue_number)
        github_comment = github_issue.create_comment(body.strip())

        # Convert to CommentData
        return CommentData(
            id=github_comment.id,
            body=github_comment.body or "",
            user=github_comment.user.login if github_comment.user else None,
            created_at=(
                github_comment.created_at.isoformat()
                if github_comment.created_at
                else None
            ),
            updated_at=(
                github_comment.updated_at.isoformat()
                if github_comment.updated_at
                else None
            ),
            url=github_comment.html_url,
        )

    @log_function_call
    @_handle_github_errors(default_return=[])
    def get_comments(self, issue_number: int) -> List[CommentData]:
        """Get all comments on an issue.

        Args:
            issue_number: Issue number to get comments from

        Returns:
            List of CommentData dictionaries with comment information, or empty list on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> comments = manager.get_comments(123)
            >>> for comment in comments:
            ...     print(f"{comment['user']}: {comment['body']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return []

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return []

        # Get issue and comments
        github_issue = repo.get_issue(issue_number)
        github_comments = github_issue.get_comments()

        # Convert to CommentData list
        comments: List[CommentData] = []
        for comment in github_comments:
            comments.append(
                CommentData(
                    id=comment.id,
                    body=comment.body or "",
                    user=comment.user.login if comment.user else None,
                    created_at=(
                        comment.created_at.isoformat() if comment.created_at else None
                    ),
                    updated_at=(
                        comment.updated_at.isoformat() if comment.updated_at else None
                    ),
                    url=comment.html_url,
                )
            )

        return comments

    @log_function_call
    @_handle_github_errors(
        default_return=CommentData(
            id=0,
            body="",
            user=None,
            created_at=None,
            updated_at=None,
            url="",
        )
    )
    def edit_comment(
        self, issue_number: int, comment_id: int, body: str
    ) -> CommentData:
        """Edit an existing comment on an issue.

        Args:
            issue_number: Issue number containing the comment
            comment_id: Comment ID to edit
            body: New comment text (required, cannot be empty)

        Returns:
            CommentData with updated comment information, or empty dict on error

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> comment = manager.edit_comment(123, 456789, "Updated comment text")
            >>> print(f"Updated comment {comment['id']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Validate comment ID
        if not self._validate_comment_id(comment_id):
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Validate body
        if not body or not body.strip():
            logger.error("Comment body cannot be empty")
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return CommentData(
                id=0,
                body="",
                user=None,
                created_at=None,
                updated_at=None,
                url="",
            )

        # Get issue to verify it exists
        github_issue = repo.get_issue(issue_number)

        # Get the comment directly from repository
        github_comment = github_issue.get_comment(comment_id)

        # Edit the comment
        github_comment.edit(body.strip())

        # Get fresh comment data after editing
        github_comment = github_issue.get_comment(comment_id)

        # Convert to CommentData
        return CommentData(
            id=github_comment.id,
            body=github_comment.body or "",
            user=github_comment.user.login if github_comment.user else None,
            created_at=(
                github_comment.created_at.isoformat()
                if github_comment.created_at
                else None
            ),
            updated_at=(
                github_comment.updated_at.isoformat()
                if github_comment.updated_at
                else None
            ),
            url=github_comment.html_url,
        )

    @log_function_call
    @_handle_github_errors(default_return=False)
    def delete_comment(self, issue_number: int, comment_id: int) -> bool:
        """Delete a comment from an issue.

        Args:
            issue_number: Issue number containing the comment
            comment_id: Comment ID to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            GithubException: For authentication or permission errors

        Example:
            >>> success = manager.delete_comment(123, 456789)
            >>> print(f"Deletion {'successful' if success else 'failed'}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return False

        # Validate comment ID
        if not self._validate_comment_id(comment_id):
            return False

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return False

        # Get issue to verify it exists
        github_issue = repo.get_issue(issue_number)

        # Get the comment directly from repository
        github_comment = github_issue.get_comment(comment_id)

        # Delete the comment
        github_comment.delete()

        return True

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
    def close_issue(self, issue_number: int) -> IssueData:
        """Close an issue.

        Args:
            issue_number: Issue number to close

        Returns:
            IssueData with updated issue information, or empty IssueData on error

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
    def reopen_issue(self, issue_number: int) -> IssueData:
        """Reopen a closed issue.

        Args:
            issue_number: Issue number to reopen

        Returns:
            IssueData with updated issue information, or empty IssueData on error

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
    @_handle_github_errors(default_return=[])
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
    def add_labels(self, issue_number: int, *labels: str) -> IssueData:
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
        if not self._validate_issue_number(issue_number):
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
    def remove_labels(self, issue_number: int, *labels: str) -> IssueData:
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
        if not self._validate_issue_number(issue_number):
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
    def set_labels(self, issue_number: int, *labels: str) -> IssueData:
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
        if not self._validate_issue_number(issue_number):
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
