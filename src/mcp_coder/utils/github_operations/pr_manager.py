"""Pull Request Manager for GitHub API operations.

This module provides the PullRequestManager class for managing GitHub pull requests
through the PyGithub library.
"""

import re
from typing import Any, Dict, List, Optional

from github import Github
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from mcp_coder.utils.log_utils import log_function_call


class PullRequestManager:
    """Manages GitHub pull request operations using the GitHub API.

    This class provides methods for creating, retrieving, listing, closing,
    and merging pull requests in a GitHub repository.
    """

    def __init__(self, repository_url: str, github_token: Optional[str] = None) -> None:
        """Initialize the PullRequestManager.

        Args:
            repository_url: GitHub repository URL (e.g., 'https://github.com/user/repo')
            github_token: GitHub personal access token for authentication

        Raises:
            ValueError: If github_token is None or empty
        """
        if not github_token:
            raise ValueError("GitHub token is required for authentication")

        self.repository_url = repository_url
        self.github_token = github_token
        self._github_client = Github(github_token)
        self._repository: Optional[Repository] = None

    def _parse_and_get_repo(self) -> Repository:
        """Parse repository URL and get Repository object.

        Returns:
            Repository: GitHub repository object

        Raises:
            ValueError: If repository URL format is invalid or repository cannot be accessed
        """
        if self._repository is not None:
            return self._repository

        # Parse repository URL to extract owner/repo
        # Support formats: https://github.com/owner/repo, git@github.com:owner/repo.git, owner/repo
        repo_pattern = (
            r"(?:https://github\.com/|git@github\.com:|^)([^/]+)/([^/\.]+)(?:\.git)?/?$"
        )
        match = re.match(repo_pattern, self.repository_url.strip())

        if not match:
            raise ValueError(
                f"Invalid GitHub repository URL format: {self.repository_url}"
            )

        owner, repo_name = match.groups()
        repo_full_name = f"{owner}/{repo_name}"

        try:
            self._repository = self._github_client.get_repo(repo_full_name)
            return self._repository
        except GithubException as e:
            raise ValueError(
                f"Failed to access repository {repo_full_name}: {e}"
            ) from e

    @log_function_call
    def create_pull_request(
        self, title: str, head_branch: str, base_branch: str = "main", body: str = ""
    ) -> Dict[str, Any]:
        """Create a new pull request.

        Args:
            title: Title of the pull request
            head_branch: Source branch for the pull request
            base_branch: Target branch for the pull request (default: "main")
            body: Description/body of the pull request

        Returns:
            Dictionary containing pull request information or empty dict on failure
        """
        try:
            repo = self._parse_and_get_repo()

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
            print(f"GitHub API error creating pull request: {e}")
            return {}
        except Exception as e:
            # Log unexpected errors and return empty dict
            print(f"Unexpected error creating pull request: {e}")
            return {}

    @log_function_call
    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Get information about a specific pull request.

        Args:
            pr_number: Pull request number

        Returns:
            Dictionary containing pull request information or empty dict on failure
        """
        try:
            repo = self._parse_and_get_repo()

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
            print(f"GitHub API error getting pull request {pr_number}: {e}")
            return {}
        except Exception as e:
            # Log unexpected errors and return empty dict
            print(f"Unexpected error getting pull request {pr_number}: {e}")
            return {}

    @log_function_call
    def list_pull_requests(
        self, state: str = "open", base_branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List pull requests in the repository.

        Args:
            state: State of pull requests to list ("open", "closed", "all")
            base_branch: Filter by base branch (optional)

        Returns:
            List of dictionaries containing pull request information or empty list on failure
        """
        try:
            repo = self._parse_and_get_repo()

            # Get pull requests using GitHub API
            # Handle optional base_branch parameter for GitHub API
            if base_branch is not None:
                prs = repo.get_pulls(state=state, base=base_branch)
            else:
                prs = repo.get_pulls(state=state)

            # Convert to structured list of dictionaries
            pr_list = []
            for pr in prs:
                pr_dict = {
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
                pr_list.append(pr_dict)

            return pr_list

        except GithubException as e:
            # Log the error and return empty list on failure
            print(f"GitHub API error listing pull requests: {e}")
            return []
        except Exception as e:
            # Log unexpected errors and return empty list
            print(f"Unexpected error listing pull requests: {e}")
            return []

    @log_function_call
    def close_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Close a pull request.

        Args:
            pr_number: Pull request number to close

        Returns:
            Dictionary containing updated pull request information or empty dict on failure
        """
        return {}

    @log_function_call
    def merge_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Merge a pull request.

        Args:
            pr_number: Pull request number to merge

        Returns:
            Dictionary containing merge result information or empty dict on failure
        """
        return {}

    @property
    def repository_name(self) -> str:
        """Get the repository name in 'owner/repo' format.

        Returns:
            Repository name or empty string on failure
        """
        return ""

    @property
    def default_branch(self) -> str:
        """Get the default branch of the repository.

        Returns:
            Default branch name or empty string on failure
        """
        return ""


def create_pr_manager(
    repository_url: str, github_token: Optional[str] = None
) -> PullRequestManager:
    """Factory function to create a PullRequestManager instance.

    Args:
        repository_url: GitHub repository URL
        github_token: GitHub personal access token for authentication

    Returns:
        PullRequestManager instance
    """
    return PullRequestManager(repository_url, github_token)
