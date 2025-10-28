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

    This decorator handles GithubException and general Exception errors:
    - Authentication/permission errors (401, 403): Re-raised to caller
    - Other GithubException errors: Logged and return default_return
    - Other exceptions: Logged and return default_return

    Args:
        default_return: Value to return when handling non-auth errors

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
                # Re-raise authentication/permission errors
                if e.status in (401, 403):
                    logger.error(
                        f"Authentication/permission error in {func.__name__}: {e}"
                    )
                    raise
                # Log and return default for other GitHub errors
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
        project_dir: Optional path to the project directory (when using local git repo)
        github_token: GitHub personal access token
        _repo: Optional GitPython repository object (None when using repo_url)
        _github_client: PyGithub client instance
        _repository: Cached GitHub repository object
        _repo_owner: Repository owner (when using repo_url)
        _repo_name: Repository name (when using repo_url)
        _repo_full_name: Full repository name "owner/repo" (when using repo_url)

    Configuration:
        Requires GitHub token in config file (~/.mcp_coder/config.toml):

        [github]
        token = "ghp_your_personal_access_token_here"

        Token needs 'repo' scope for private repositories, 'public_repo' for public.
    """

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
    ) -> None:
        """Initialize the BaseGitHubManager.

        Can be initialized with either a local git repository (project_dir) or
        a GitHub repository URL (repo_url). Exactly one must be provided.

        Args:
            project_dir: Path to the project directory containing git repository
            repo_url: GitHub repository URL (e.g., "https://github.com/user/repo.git")

        Raises:
            ValueError: If neither or both parameters provided, directory doesn't exist,
                       is not a directory, is not a git repository,
                       or GitHub token is not configured
        """
        # Validate exactly one parameter provided
        if (project_dir is None) == (repo_url is None):
            raise ValueError("Exactly one of project_dir or repo_url must be provided")

        # Get GitHub token
        github_token = user_config.get_config_value("github", "token")
        if not github_token:
            raise ValueError(
                "GitHub token not found. Configure it in ~/.mcp_coder/config.toml "
                "or set GITHUB_TOKEN environment variable"
            )

        # Initialize GitHub client
        self.github_token = github_token
        self._github_client = Github(github_token)
        self._repository: Optional[Repository] = None

        # Initialize attributes that may be set by helper methods
        self.project_dir: Optional[Path] = None
        self._repo: Optional[git.Repo] = None
        self._repo_owner: Optional[str] = None
        self._repo_name: Optional[str] = None
        self._repo_full_name: Optional[str] = None

        # Initialize based on mode
        if project_dir is not None:
            self._init_with_project_dir(project_dir)
        else:
            self._init_with_repo_url(repo_url)  # type: ignore[arg-type]

    def _init_with_project_dir(self, project_dir: Path) -> None:
        """Initialize with local git repository (existing behavior).

        Args:
            project_dir: Path to the project directory containing git repository

        Raises:
            ValueError: If directory doesn't exist, is not a directory,
                       or is not a git repository
        """
        # Validate project_dir
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

        # Initialize attributes for project_dir mode
        self.project_dir = project_dir
        self._repo = repo
        self._repo_owner = None
        self._repo_name = None
        self._repo_full_name = None

    def _init_with_repo_url(self, repo_url: str) -> None:
        """Initialize with GitHub repository URL (new behavior).

        Args:
            repo_url: GitHub repository URL (e.g., "https://github.com/user/repo.git")

        Raises:
            ValueError: If repo_url format is invalid
        """
        # Parse repo_url to extract owner/repo
        parsed = parse_github_url(repo_url)
        if parsed is None:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

        owner, repo_name = parsed

        # Initialize attributes for repo_url mode
        self.project_dir = None
        self._repo = None
        self._repo_owner = owner
        self._repo_name = repo_name
        self._repo_full_name = f"{owner}/{repo_name}"

    @log_function_call
    def _get_repository(self) -> Optional[Repository]:
        """Get the GitHub repository object.

        Uses cached repository if available, otherwise retrieves it from
        the GitHub API using either the git remote URL (project_dir mode)
        or the stored repo_full_name (repo_url mode).

        Returns:
            Repository object if successful, None otherwise

        Note:
            The repository object is cached after the first successful retrieval
            to avoid unnecessary API calls.
        """
        if self._repository is not None:
            return self._repository

        try:
            repo_full_name = None

            # Determine repo_full_name based on initialization mode
            if self._repo_full_name is not None:
                # repo_url mode - use stored value
                repo_full_name = self._repo_full_name
            elif self._repo is not None:
                # project_dir mode - extract from git remote
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

            if not repo_full_name:
                logger.warning("Could not determine repository full name")
                return None

            # Get repository from GitHub API
            self._repository = self._github_client.get_repo(repo_full_name)
            return self._repository

        except GithubException as e:
            logger.error("Failed to access repository: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error accessing repository: %s", e)
            return None
