"""Pull Request Manager for GitHub API operations.

This module provides the PullRequestManager class for managing GitHub pull requests
through the PyGithub library.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from github import Github
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from mcp_coder.utils.log_utils import log_function_call

# Configure logger for GitHub operations
logger = logging.getLogger(__name__)


class PullRequestManager:
    """Manages GitHub pull request operations using the GitHub API.

    This class provides methods for creating, retrieving, listing, closing,
    and merging pull requests in a GitHub repository.
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        """Initialize the PullRequestManager.

        Args:
            project_dir: Path to the project directory containing git repository

        Raises:
            ValueError: If project_dir is None, directory doesn't exist, is not a git repository,
                       has no GitHub remote origin, or GitHub token is not configured
        """
        from mcp_coder.utils.git_operations import get_github_repository_url, is_git_repository
        from mcp_coder.utils.user_config import get_config_value

        # 1. Check if project_dir is provided
        if project_dir is None:
            raise ValueError("project_dir is required. Please specify the path to your git repository.")
        
        # 2. Check if directory exists
        if not project_dir.exists():
            raise ValueError(f"Directory does not exist: {project_dir}")
        
        # 3. Check if it's actually a directory (not a file)
        if not project_dir.is_dir():
            raise ValueError(f"Path is not a directory: {project_dir}")
        
        # 4. Check if it's a git repository
        if not is_git_repository(project_dir):
            raise ValueError(f"Directory is not a git repository: {project_dir}")
        
        # 5. Try to get GitHub repository URL
        repository_url = get_github_repository_url(project_dir)
        if repository_url is None:
            raise ValueError(
                f"Could not detect GitHub repository URL from git remote in: {project_dir}. "
                "Make sure the repository has a GitHub remote origin configured."
            )
        
        # 6. Check if GitHub token is available
        github_token = get_config_value("github", "token")
        if not github_token:
            raise ValueError(
                "GitHub token not found in configuration. "
                "Please add your GitHub token to ~/.mcp_coder/config.toml under [github] token = \"your_token\""
            )
        
        # All validations passed - initialize
        self.project_dir = project_dir
        self.repository_url = repository_url
        self.github_token = github_token
        self._github_client = Github(github_token)
        self._repository: Optional[Repository] = None

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

    def _parse_and_get_repo(self) -> Optional[Repository]:
        """Parse repository URL and get Repository object.

        Returns:
            Repository object if successful, None if any error occurs
        """
        if self._repository is not None:
            return self._repository

        try:
            # Parse repository URL to extract owner/repo
            # Support formats: https://github.com/owner/repo, git@github.com:owner/repo.git, owner/repo
            repo_pattern = r"(?:https://github\.com/|git@github\.com:|^)([^/]+)/([^/\.]+)(?:\.git)?/?$"
            match = re.match(repo_pattern, self.repository_url.strip())

            if not match:
                logger.error(
                    f"Invalid GitHub repository URL format: {self.repository_url}"
                )
                return None

            owner, repo_name = match.groups()
            repo_full_name = f"{owner}/{repo_name}"

            self._repository = self._github_client.get_repo(repo_full_name)
            return self._repository
        except GithubException as e:
            logger.error(f"Failed to access repository: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error accessing repository: {e}")
            return None

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
        # Validate branch names
        if not self._validate_branch_name(head_branch):
            return {}
        if not self._validate_branch_name(base_branch):
            return {}

        try:
            repo = self._parse_and_get_repo()
            if repo is None:
                return {}

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
        # Validate PR number
        if not self._validate_pr_number(pr_number):
            return {}

        try:
            repo = self._parse_and_get_repo()
            if repo is None:
                return {}

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
        # Validate base_branch if provided
        if base_branch is not None and not self._validate_branch_name(base_branch):
            return []

        try:
            repo = self._parse_and_get_repo()
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
            for pr in prs:
                # TODO - should we have a typed dict for that? / same  below?
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
        # Validate PR number
        if not self._validate_pr_number(pr_number):
            return {}

        try:
            repo = self._parse_and_get_repo()
            if repo is None:
                return {}

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
            print(f"GitHub API error closing pull request {pr_number}: {e}")
            return {}
        except Exception as e:
            # Log unexpected errors and return empty dict
            print(f"Unexpected error closing pull request {pr_number}: {e}")
            return {}

    # not used so far, could be removed
    @log_function_call
    def merge_pull_request(
        self,
        pr_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """Merge a pull request.

        Args:
            pr_number: Pull request number to merge
            commit_title: Optional custom commit title for the merge
            commit_message: Optional custom commit message for the merge
            merge_method: Merge method to use ("merge", "squash", "rebase")

        Returns:
            Dictionary containing merge result information or empty dict on failure
        """
        # Validate PR number
        if not self._validate_pr_number(pr_number):
            return {}

        # Validate merge method
        valid_merge_methods = ["merge", "squash", "rebase"]
        if merge_method not in valid_merge_methods:
            logger.error(
                f"Invalid merge method '{merge_method}'. Must be one of: {valid_merge_methods}"
            )
            return {}

        try:
            repo = self._parse_and_get_repo()
            if repo is None:
                return {}

            # Get the pull request using GitHub API
            pr = repo.get_pull(pr_number)

            # Check if PR is mergeable
            if not pr.mergeable:
                print(f"Pull request {pr_number} is not mergeable")
                return {}

            if pr.merged:
                print(f"Pull request {pr_number} is already merged")
                return {
                    "merged": True,
                    "message": "Pull request was already merged",
                    "sha": pr.merge_commit_sha,
                    "number": pr_number,
                }

            # Merge the pull request using GitHub API
            # Handle optional commit title and message parameters
            # Note: PyGithub's merge method signature varies by version
            # The merge_method parameter is primarily for documentation/validation

            # Log the merge method for debugging
            logger.info(f"Merging PR {pr_number} using method '{merge_method}'")

            # Perform the merge with proper parameter handling
            if commit_title is not None and commit_message is not None:
                merge_result = pr.merge(commit_title, commit_message)
            elif commit_title is not None:
                merge_result = pr.merge(commit_title)
            else:
                merge_result = pr.merge()

            # Return structured dictionary with merge result information
            return {
                "merged": merge_result.merged,
                "message": merge_result.message,
                "sha": merge_result.sha,
                "number": pr_number,
            }

        except GithubException as e:
            # Log the error and return empty dict on failure
            print(f"GitHub API error merging pull request {pr_number}: {e}")
            return {}
        except Exception as e:
            # Log unexpected errors and return empty dict
            print(f"Unexpected error merging pull request {pr_number}: {e}")
            return {}

    # should this be taken from git_operations
    @property
    def repository_name(self) -> str:
        """Get the repository name in 'owner/repo' format.

        Returns:
            Repository name or empty string on failure
        """
        try:
            repo = self._parse_and_get_repo()
            if repo is None:
                return ""
            return repo.full_name
        except Exception as e:
            print(f"Error getting repository name: {e}")
            return ""

    # TODO - use functionality of git_operations
    @property
    def default_branch(self) -> str:
        """Get the default branch of the repository.

        Returns:
            Default branch name or empty string on failure
        """
        try:
            repo = self._parse_and_get_repo()
            if repo is None:
                return ""
            return repo.default_branch
        except Exception as e:
            print(f"Error getting default branch: {e}")
            return ""
