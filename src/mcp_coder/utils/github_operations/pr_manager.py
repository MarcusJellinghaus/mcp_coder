"""Pull Request Manager for GitHub API operations.

This module provides the PullRequestManager class for managing GitHub pull requests
through the PyGithub library.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, cast

from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from mcp_coder.utils import (
    get_default_branch_name,
    get_github_repository_url,
)
from mcp_coder.utils.log_utils import log_function_call

from .base_manager import BaseGitHubManager, _handle_github_errors
from .github_utils import parse_github_url

# Configure logger for GitHub operations
logger = logging.getLogger(__name__)


class PullRequestData(TypedDict):
    """TypedDict for pull request data structure."""

    number: int
    title: str
    body: str
    state: str
    head_branch: str
    base_branch: str
    url: str
    created_at: Optional[str]
    updated_at: Optional[str]
    user: Optional[str]
    mergeable: Optional[bool]
    merged: bool
    draft: bool


class PullRequestManager(BaseGitHubManager):
    """Manages GitHub pull request operations using the GitHub API.

    This class provides methods for creating, retrieving, listing, closing,
    and merging pull requests in a GitHub repository.

    Configuration:
        Requires GitHub token in config file (~/.mcp_coder/config.toml):

        [github]
        token = "ghp_your_personal_access_token_here"

        Token needs 'repo' scope for private repositories, 'public_repo' for public.
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        """Initialize the PullRequestManager.

        Args:
            project_dir: Path to the project directory containing git repository

        Raises:
            ValueError: If project_dir is None, directory doesn't exist, is not a git repository,
                       has no GitHub remote origin, or GitHub token is not configured
        """
        super().__init__(project_dir)

        # Store repository URL for compatibility with existing code
        # At this point, project_dir is guaranteed to be valid (checked by super().__init__)
        self.repository_url = get_github_repository_url(self.project_dir)
        if self.repository_url is None:
            raise ValueError(
                f"Could not detect GitHub repository URL from git remote in: {self.project_dir}. "
                "Make sure the repository has a GitHub remote origin configured."
            )

    def _validate_pr_number(self, pr_number: int) -> bool:
        """Validate pull request number.

        Args:
            pr_number: Pull request number to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(pr_number, int) or pr_number <= 0:
            logger.error(f"Invalid PR number: {pr_number}. Must be a positive integer.")
            return False
        return True

    def _validate_branch_name(self, branch_name: str) -> bool:
        """Validate branch name.

        Args:
            branch_name: Branch name to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(branch_name, str) or not branch_name.strip():
            logger.error(
                f"Invalid branch name: '{branch_name}'. Must be a non-empty string."
            )
            return False
        # GitHub branch name restrictions
        invalid_chars = ["~", "^", ":", "?", "*", "["]
        if any(char in branch_name for char in invalid_chars):
            logger.error(
                f"Invalid branch name: '{branch_name}'. Contains invalid characters: {invalid_chars}"
            )
            return False
        if (
            branch_name.startswith(".")
            or branch_name.endswith(".")
            or branch_name.endswith(".lock")
        ):
            logger.error(
                f"Invalid branch name: '{branch_name}'. Cannot start/end with '.' or end with '.lock'"
            )
            return False
        return True

    @log_function_call
    @_handle_github_errors(lambda: cast(PullRequestData, {}))
    def create_pull_request(
        self, title: str, head_branch: str, base_branch: str = "main", body: str = ""
    ) -> PullRequestData:
        """Create a new pull request.

        Args:
            title: Title of the pull request (must be non-empty)
            head_branch: Source branch for the pull request
            base_branch: Target branch for the pull request (default: "main")
            body: Description/body of the pull request (optional)

        Returns:
            PullRequestData containing pull request information or empty dict on failure.

            Success response includes:
            - number: PR number (int)
            - title: PR title (str)
            - body: PR description (str)
            - state: PR state, typically "open" (str)
            - head_branch: Source branch name (str)
            - base_branch: Target branch name (str)
            - url: GitHub URL to the PR (str)
            - created_at: ISO timestamp (str)
            - updated_at: ISO timestamp (str)
            - user: GitHub username of creator (str)
            - mergeable: Whether PR can be merged (bool)
            - merged: Whether PR is already merged (bool)
            - draft: Whether PR is a draft (bool)
        """
        # Validate title
        if not isinstance(title, str) or not title.strip():
            logger.error(f"Invalid PR title: '{title}'. Must be a non-empty string.")
            return cast(PullRequestData, {})

        # Validate branch names
        if not self._validate_branch_name(head_branch):
            return cast(PullRequestData, {})
        if not self._validate_branch_name(base_branch):
            return cast(PullRequestData, {})

        try:
            repo = self._get_repository()
            if repo is None:
                return cast(PullRequestData, {})

            # Create the pull request using GitHub API
            pr = repo.create_pull(
                title=title, body=body, head=head_branch, base=base_branch
            )

            # Return structured dictionary with PR information
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "head_branch": pr.head.ref,
                "base_branch": pr.base.ref,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "user": pr.user.login if pr.user else None,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "draft": pr.draft,
            }

        except GithubException as e:
            # Log the error and return empty dict on failure
            logger.error(f"GitHub API error creating pull request: {e}")
            return cast(PullRequestData, {})

    @log_function_call
    @_handle_github_errors(lambda: cast(PullRequestData, {}))
    def get_pull_request(self, pr_number: int) -> PullRequestData:
        """Get information about a specific pull request.

        Args:
            pr_number: Pull request number

        Returns:
            PullRequestData containing pull request information or empty dict on failure
        """
        # Validate PR number
        if not self._validate_pr_number(pr_number):
            return cast(PullRequestData, {})

        try:
            repo = self._get_repository()
            if repo is None:
                return cast(PullRequestData, {})

            # Get the pull request using GitHub API
            pr = repo.get_pull(pr_number)

            # Return structured dictionary with PR information
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "head_branch": pr.head.ref,
                "base_branch": pr.base.ref,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "user": pr.user.login if pr.user else None,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "draft": pr.draft,
            }

        except GithubException as e:
            # Log the error and return empty dict on failure
            logger.error(f"GitHub API error getting pull request {pr_number}: {e}")
            return cast(PullRequestData, {})

    @log_function_call
    @_handle_github_errors(lambda: [])
    def list_pull_requests(
        self, state: str = "open", base_branch: Optional[str] = None, max_results: Optional[int] = None
    ) -> List[PullRequestData]:
        """List pull requests in the repository.

        Args:
            state: State of pull requests to list ("open", "closed", "all")
            base_branch: Filter by base branch (optional)
            max_results: Maximum number of results to return (optional, returns all if None)

        Returns:
            List of PullRequestData containing pull request information or empty list on failure.
            Each item in the list has the same structure as create_pull_request() return value.
        """
        # Validate base_branch if provided
        if base_branch is not None and not self._validate_branch_name(base_branch):
            return []

        try:
            repo = self._get_repository()
            if repo is None:
                return []

            # Get pull requests using GitHub API
            # Handle optional base_branch parameter for GitHub API
            if base_branch is not None:
                prs = repo.get_pulls(state=state, base=base_branch)
            else:
                prs = repo.get_pulls(state=state)

            # Convert to structured list of dictionaries
            pr_list = []
            for i, pr in enumerate(prs):
                # Stop if we've reached max_results limit
                if max_results is not None and i >= max_results:
                    break
                    
                pr_dict = cast(
                    PullRequestData,
                    {
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body,
                        "state": pr.state,
                        "head_branch": pr.head.ref,
                        "base_branch": pr.base.ref,
                        "url": pr.html_url,
                        "created_at": (
                            pr.created_at.isoformat() if pr.created_at else None
                        ),
                        "updated_at": (
                            pr.updated_at.isoformat() if pr.updated_at else None
                        ),
                        "user": pr.user.login if pr.user else None,
                        "mergeable": pr.mergeable,
                        "merged": pr.merged,
                        "draft": pr.draft,
                    },
                )
                pr_list.append(pr_dict)

            return pr_list

        except GithubException as e:
            # Log the error and return empty list on failure
            logger.error(f"GitHub API error listing pull requests: {e}")
            return []

    @log_function_call
    @_handle_github_errors(lambda: cast(PullRequestData, {}))
    def close_pull_request(self, pr_number: int) -> PullRequestData:
        """Close a pull request.

        Args:
            pr_number: Pull request number to close

        Returns:
            PullRequestData containing updated pull request information or empty dict on failure
        """
        # Validate PR number
        if not self._validate_pr_number(pr_number):
            return cast(PullRequestData, {})

        try:
            repo = self._get_repository()
            if repo is None:
                return cast(PullRequestData, {})

            # Get the pull request using GitHub API
            pr = repo.get_pull(pr_number)

            # Close the pull request by editing it
            pr.edit(state="closed")

            # Get updated PR information after closing
            updated_pr = repo.get_pull(pr_number)

            # Return structured dictionary with updated PR information
            return {
                "number": updated_pr.number,
                "title": updated_pr.title,
                "body": updated_pr.body,
                "state": updated_pr.state,
                "head_branch": updated_pr.head.ref,
                "base_branch": updated_pr.base.ref,
                "url": updated_pr.html_url,
                "created_at": (
                    updated_pr.created_at.isoformat() if updated_pr.created_at else None
                ),
                "updated_at": (
                    updated_pr.updated_at.isoformat() if updated_pr.updated_at else None
                ),
                "user": updated_pr.user.login if updated_pr.user else None,
                "mergeable": updated_pr.mergeable,
                "merged": updated_pr.merged,
                "draft": updated_pr.draft,
            }

        except GithubException as e:
            # Log the error and return empty dict on failure
            logger.error(f"GitHub API error closing pull request {pr_number}: {e}")
            return cast(PullRequestData, {})

    @property
    def repository_name(self) -> str:
        """Get the repository name in 'owner/repo' format.

        Returns:
            Repository name in format "owner/repo" or empty string on failure
        """
        from .github_utils import get_repo_full_name

        try:
            # repository_url is set in __init__ and guaranteed to be non-None
            if self.repository_url is None:
                return ""
            repo_name = get_repo_full_name(self.repository_url)
            return repo_name or ""
        except Exception as e:
            logger.debug(f"Error getting repository name: {e}")
            return ""

    @property
    def default_branch(self) -> str:
        """Get the default branch of the repository.

        Returns:
            Default branch name (typically "main" or "master") or empty string on failure
        """
        try:
            default_branch = get_default_branch_name(self.project_dir)
            return default_branch or ""
        except Exception as e:
            logger.debug(f"Error getting default branch: {e}")
            return ""
