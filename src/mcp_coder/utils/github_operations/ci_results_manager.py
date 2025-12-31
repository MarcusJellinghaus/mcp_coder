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

    @log_function_call
    @_handle_github_errors(default_return=CIStatusData(run={}, jobs=[]))
    def get_latest_ci_status(self, branch: str) -> CIStatusData:
        """Get latest CI run status and job results for a branch.

        Args:
            branch: Branch name (required, e.g., 'feature/xyz', 'main')

        Returns:
            CIStatusData with run info and all job statuses

        Raises:
            ValueError: For invalid branch names
            GithubException: For authentication or permission errors
        """
        # Validate branch parameter
        if not branch or not branch.strip():
            raise ValueError("Invalid branch name: branch name cannot be empty")

        if not self._validate_branch_name(branch.strip()):
            raise ValueError(f"Invalid branch name: '{branch}'")

        branch = branch.strip()

        # Get repository
        repo = self._get_repository()
        if not repo:
            logger.error("Could not access GitHub repository")
            return CIStatusData(run={}, jobs=[])

        # Get workflow runs for the branch
        try:
            # Get all workflow runs and filter by branch
            all_runs = repo.get_workflow_runs()
            runs_list = [run for run in all_runs if run.head_branch == branch]

            if not runs_list:
                logger.info(f"No workflow runs found for branch: {branch}")
                return CIStatusData(run={}, jobs=[])

            # Get the latest run (first in the list)
            latest_run = runs_list[0]

            # Get all jobs for the latest run
            jobs = list(latest_run.jobs())

            # Transform run data
            run_data = {
                "id": latest_run.id,
                "status": latest_run.status,
                "conclusion": latest_run.conclusion,
                "workflow_name": latest_run.name,
                "event": latest_run.event,
                "workflow_path": latest_run.path,
                "branch": branch,
                "commit_sha": latest_run.head_sha,
                "created_at": (
                    latest_run.created_at.isoformat() if latest_run.created_at else None
                ),
                "url": latest_run.html_url,
            }

            # Transform job data
            jobs_data = []
            for job in jobs:
                job_data = {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "conclusion": job.conclusion,
                    "started_at": (
                        job.started_at.isoformat() if job.started_at else None
                    ),
                    "completed_at": (
                        job.completed_at.isoformat() if job.completed_at else None
                    ),
                }
                jobs_data.append(job_data)

            return CIStatusData(run=run_data, jobs=jobs_data)

        except Exception as e:
            logger.error(f"Error retrieving CI status for branch {branch}: {e}")
            # Re-raise to let the decorator handle it
            raise
