"""Base manager class for GitHub operations.

This module provides the BaseGitHubManager class that contains shared
functionality for all GitHub manager classes.
"""

import functools
import logging
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast

import git
from github import Github
from github.GithubException import GithubException
from github.Repository import Repository

from mcp_coder.utils import user_config
from mcp_coder.utils.log_utils import log_function_call

from .github_utils import parse_github_url

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _handle_github_errors(
    default_return: Any,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to handle GitHub API errors consistently.

    This decorator handles GithubException and general Exception errors by
    logging them and returning the default_return value.

    Args:
        default_return: Value to return when handling errors

    Returns:
        Decorator function that wraps the original function with error handling

    Example:
        @_handle_github_errors(default_return={})
        def create_issue(self, title: str) -> IssueData:
            # Implementation that may raise GithubException
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except GithubException as e:
                # Log and return default for GitHub errors
                logger.error(f"GitHub API error in {func.__name__}: {e}")
                return cast(T, default_return)
            except Exception as e:
                # Log and return default for unexpected errors
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return cast(T, default_return)

        return wrapper

    return decorator


class BaseGitHubManager:
    """Base class for GitHub managers.

    Provides common initialization and validation logic for GitHub API operations.
    All GitHub manager classes should inherit from this base class.

    Attributes:
        project_dir: Path to the project directory
        github_token: GitHub personal access token
        _repo: GitPython repository object
        _github_client: PyGithub client instance
        _repository: Cached GitHub repository object

    Configuration:
        Requires GitHub token in config file (~/.mcp_coder/config.toml):

        [github]
        token = "ghp_your_personal_access_token_here"

        Token needs 'repo' scope for private repositories, 'public_repo' for public.
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        """Initialize the BaseGitHubManager.

        Validates the project directory, ensures it's a git repository,
        retrieves the GitHub token, and initializes the GitHub client.

        Args:
            project_dir: Path to the project directory containing git repository

        Raises:
            ValueError: If project_dir is None, directory doesn't exist,
                       is not a directory, is not a git repository,
                       or GitHub token is not configured
        """
        # Validate project_dir
        if project_dir is None:
            raise ValueError("project_dir is required")

        if not project_dir.exists():
            raise ValueError(f"Directory does not exist: {project_dir}")

        if not project_dir.is_dir():
            raise ValueError(f"Path is not a directory: {project_dir}")

        # Check if it's a git repository
        try:
            repo = git.Repo(project_dir)
        except git.InvalidGitRepositoryError as exc:
            raise ValueError(
                f"Directory is not a git repository: {project_dir}"
            ) from exc

        # Get GitHub token
        github_token = user_config.get_config_value("github", "token")
        if not github_token:
            raise ValueError(
                "GitHub token not found. Configure it in ~/.mcp_coder/config.toml "
                "or set GITHUB_TOKEN environment variable"
            )

        # Initialize attributes
        self.project_dir = project_dir
        self.github_token = github_token
        self._repo = repo
        self._github_client = Github(github_token)
        self._repository: Optional[Repository] = None

    @log_function_call
    def _get_repository(self) -> Optional[Repository]:
        """Get the GitHub repository object.

        Uses cached repository if available, otherwise retrieves it from
        the GitHub API using the git remote URL.

        Returns:
            Repository object if successful, None otherwise

        Note:
            The repository object is cached after the first successful retrieval
            to avoid unnecessary API calls.
        """
        if self._repository is not None:
            return self._repository

        try:
            # Get the remote URL from git repository
            remote_url = None
            for remote in self._repo.remotes:
                if remote.name == "origin":
                    remote_url = remote.url
                    break

            if not remote_url:
                logger.warning("No 'origin' remote found in git repository")
                return None

            # Parse the GitHub URL
            parsed = parse_github_url(remote_url)
            if parsed is None:
                logger.warning("Could not parse GitHub URL: %s", remote_url)
                return None

            owner, repo_name = parsed
            repo_full_name = f"{owner}/{repo_name}"

            # Get repository from GitHub API
            self._repository = self._github_client.get_repo(repo_full_name)
            return self._repository

        except GithubException as e:
            logger.error("Failed to access repository: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error accessing repository: %s", e)
            return None
