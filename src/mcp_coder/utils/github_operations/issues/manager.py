"""Issue Manager for GitHub API operations.

This module provides the IssueManager class that composes all mixin classes
for managing GitHub issues through the PyGithub library.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from mcp_coder.utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.github_operations.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.log_utils import log_function_call

from ..base_manager import BaseGitHubManager, _handle_github_errors
from .base import parse_base_branch, validate_issue_number
from .branch_manager import IssueBranchManager
from .comments_mixin import CommentsMixin
from .events_mixin import EventsMixin
from .labels_mixin import LabelsMixin
from .types import IssueData, create_empty_issue_data

logger = logging.getLogger(__name__)

__all__ = ["IssueManager"]


class IssueManager(CommentsMixin, LabelsMixin, EventsMixin, BaseGitHubManager):
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

    @log_function_call
    @_handle_github_errors(default_return=create_empty_issue_data())
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
            ValueError: If title is empty
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
            raise ValueError("Issue title cannot be empty")

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return create_empty_issue_data()

        # Create issue
        if labels:
            github_issue = repo.create_issue(
                title=title.strip(), body=body, labels=labels
            )
        else:
            github_issue = repo.create_issue(title=title.strip(), body=body)

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
    @_handle_github_errors(default_return=create_empty_issue_data())
    def get_issue(self, issue_number: int) -> IssueData:
        """Retrieve issue details by number.

        Args:
            issue_number: Issue number to retrieve

        Returns:
            IssueData with issue information, or empty IssueData on error

        Raises:
            ValueError: If issue number is invalid
            GithubException: For authentication or permission errors

        Example:
            >>> issue = manager.get_issue(123)
            >>> print(f"Issue: {issue['title']}")
            >>> print(f"Assignees: {issue['assignees']}")
        """
        # Validate issue number
        validate_issue_number(issue_number)

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return create_empty_issue_data()

        # Get issue
        github_issue = repo.get_issue(issue_number)

        # Parse base_branch from body
        body = github_issue.body or ""
        try:
            base_branch = parse_base_branch(body)
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
                base_branch = parse_base_branch(body)
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
    @_handle_github_errors(default_return=create_empty_issue_data())
    def close_issue(self, issue_number: int) -> IssueData:
        """Close an issue.

        Args:
            issue_number: Issue number to close

        Returns:
            IssueData with updated issue information, or empty IssueData on error

        Raises:
            ValueError: If issue number is invalid
            GithubException: For authentication or permission errors

        Example:
            >>> closed_issue = manager.close_issue(123)
            >>> print(f"Issue state: {closed_issue['state']}")
        """
        # Validate issue number
        validate_issue_number(issue_number)

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return create_empty_issue_data()

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
    @_handle_github_errors(default_return=create_empty_issue_data())
    def reopen_issue(self, issue_number: int) -> IssueData:
        """Reopen a closed issue.

        Args:
            issue_number: Issue number to reopen

        Returns:
            IssueData with updated issue information, or empty IssueData on error

        Raises:
            ValueError: If issue number is invalid
            GithubException: For authentication or permission errors

        Example:
            >>> reopened_issue = manager.reopen_issue(123)
            >>> print(f"Issue state: {reopened_issue['state']}")
        """
        # Validate issue number
        validate_issue_number(issue_number)

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return create_empty_issue_data()

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
                        f"Branch '{actual_branch_name}' does not follow "
                        "{issue_number}-title pattern"
                    )
                    return False
                issue_number = extracted_issue_number

                # Step 3: Verify branch is linked to the issue
                # Construct repo_url from _repo_full_name if available,
                # otherwise use project_dir
                repo_url = None
                if self._repo_full_name is not None:
                    repo_url = f"https://github.com/{self._repo_full_name}.git"

                branch_manager = IssueBranchManager(
                    project_dir=self.project_dir, repo_url=repo_url
                )
                linked_branches = branch_manager.get_linked_branches(issue_number)

                if actual_branch_name not in linked_branches:
                    logger.warning(
                        f"Branch '{actual_branch_name}' is not linked to "
                        f"issue #{issue_number}. "
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
                    f"Source label '{from_label_name}' not present on "
                    f"issue #{issue_number}. "
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
