"""CI Results Manager for GitHub API operations.

This module provides data structures and the CIResultsManager class for managing
GitHub CI pipeline results through the PyGithub library.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from mcp_coder.utils.git_operations.branches import validate_branch_name
from mcp_coder.utils.log_utils import log_function_call

from .base_manager import BaseGitHubManager, _handle_github_errors

logger = logging.getLogger(__name__)

__all__ = [
    "CIStatusData",
    "CIResultsManager",
]


class CIStatusData(TypedDict):
    """TypedDict for CI status data structure.

    Represents a GitHub workflow run with its associated jobs.
    """

    run: Dict[
        str, Any
    ]  # {id, status, conclusion, workflow_name, event, workflow_path, branch, commit_sha, created_at, url}
    jobs: List[
        Dict[str, Any]
    ]  # [{id, name, status, conclusion, started_at, completed_at}]


class CIResultsManager(BaseGitHubManager):
    """Manages GitHub CI pipeline results using the GitHub API.

    This class provides methods for retrieving CI status, failed job logs,
    and artifacts from GitHub workflow runs.

    Configuration:
        Requires GitHub token in config file (~/.mcp_coder/config.toml):

        [github]
        token = "ghp_your_personal_access_token_here"

        Token needs 'repo' scope for private repositories, 'public_repo' for public.
    """

    def __init__(
        self, project_dir: Optional[Path] = None, repo_url: Optional[str] = None
    ) -> None:
        """Initialize the CIResultsManager.

        Args:
            project_dir: Path to the project directory containing git repository
            repo_url: GitHub repository URL (e.g., "https://github.com/user/repo.git")

        Raises:
            ValueError: If neither or both parameters provided, directory doesn't exist,
                       is not a git repository, or GitHub token is not configured
        """
        super().__init__(project_dir=project_dir, repo_url=repo_url)

    def _validate_branch_name(self, branch: str) -> bool:
        """Validate branch name using git naming rules.

        Args:
            branch: Branch name to validate

        Returns:
            True if valid, False otherwise
        """
        if not validate_branch_name(branch):
            logger.error(f"Invalid branch name: '{branch}'")
            return False
        return True

    def _validate_run_id(self, run_id: int) -> bool:
        """Validate workflow run ID.

        Args:
            run_id: Workflow run ID to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(run_id, int) or run_id <= 0:
            logger.error(f"Invalid run ID: {run_id}. Must be a positive integer.")
            return False
        return True
