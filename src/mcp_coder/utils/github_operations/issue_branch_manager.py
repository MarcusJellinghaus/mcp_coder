"""Branch management operations for GitHub issues."""

import logging
import re
from pathlib import Path
from typing import List, Optional, TypedDict

from mcp_coder.utils.log_utils import log_function_call

from .base_manager import BaseGitHubManager, _handle_github_errors

# Configure logger for GitHub operations
logger = logging.getLogger(__name__)


class BranchCreationResult(TypedDict):
    """TypedDict for branch creation result.

    Represents the result of a branch creation operation with all relevant fields.
    """

    success: bool
    branch_name: str
    error: Optional[str]
    existing_branches: List[str]


def generate_branch_name_from_issue(
    issue_number: int, issue_title: str, max_length: int = 200
) -> str:
    """Generate sanitized branch name matching GitHub's native rules.

    Args:
        issue_number: Issue number (e.g., 123)
        issue_title: Raw issue title (e.g., "Add New Feature - Part 1")
        max_length: Max branch name length in characters (default 200)

    Returns:
        Sanitized branch name (e.g., "123-add-new-feature---part-1")
    """
    # Step 1: Replace " - " with "---" (GitHub-specific rule)
    sanitized = issue_title.replace(" - ", "---")

    # Step 2: Convert to lowercase
    sanitized = sanitized.lower()

    # Step 3: Replace non-alphanumeric (except dash) with dash
    sanitized = re.sub(r"[^a-z0-9-]+", "-", sanitized)

    # Step 4: Replace multiple consecutive dashes with single dash
    # (but preserve "---" from step 1)
    # First, protect "---" by temporarily replacing it
    sanitized = sanitized.replace("---", "\x00")
    sanitized = re.sub(r"-+", "-", sanitized)
    sanitized = sanitized.replace("\x00", "---")

    # Step 5: Strip leading/trailing dashes
    sanitized = sanitized.strip("-")

    # Step 6: Truncate to max_length if needed
    branch_prefix = f"{issue_number}-"
    if sanitized:
        full_branch_name = f"{branch_prefix}{sanitized}"
    else:
        # Handle empty title case
        full_branch_name = str(issue_number)

    if len(full_branch_name) > max_length:
        # Keep issue number prefix and truncate title
        available_for_title = max_length - len(branch_prefix)
        if available_for_title > 0:
            truncated_title = sanitized[:available_for_title].rstrip("-")
            full_branch_name = f"{branch_prefix}{truncated_title}"
        else:
            # If even the prefix is too long, just return the issue number
            full_branch_name = str(issue_number)

    return full_branch_name


class IssueBranchManager(BaseGitHubManager):
    """Manages GitHub issue-branch linking operations using GraphQL API.

    This class provides methods for creating, querying, and managing
    branch-issue associations that appear in GitHub's "Development" section.

    Configuration:
        Requires GitHub token in config file (~/.mcp_coder/config.toml):

        [github]
        token = "ghp_your_personal_access_token_here"

        Token needs 'repo' scope for private repositories, 'public_repo' for public.
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        """Initialize the IssueBranchManager.

        Args:
            project_dir: Path to the project directory containing git repository

        Raises:
            ValueError: If project_dir is None, directory doesn't exist,
                       is not a git repository, or GitHub token is not configured
        """
        super().__init__(project_dir)

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

    @log_function_call
    @_handle_github_errors(default_return=[])
    def get_linked_branches(self, issue_number: int) -> List[str]:
        """Query linked branches for an issue via GraphQL.

        Args:
            issue_number: Issue number to query linked branches for

        Returns:
            List of branch names linked to the issue, or empty list on error

        Example:
            >>> manager = IssueBranchManager(Path.cwd())
            >>> branches = manager.get_linked_branches(123)
            >>> print(f"Linked branches: {branches}")
            ['123-feature-branch', '123-hotfix']
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return []

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return []

        # Extract owner and repo name
        owner, repo_name = repo.owner.login, repo.name

        # GraphQL query for linked branches
        query = """
        query($owner: String!, $repo: String!, $issueNumber: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $issueNumber) {
              linkedBranches(first: 100) {
                nodes {
                  ref {
                    name
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            "owner": owner,
            "repo": repo_name,
            "issueNumber": issue_number,
        }

        # Execute GraphQL query
        # Note: Using private attribute is the documented way to access GraphQL in PyGithub
        result = self._github_client._Github__requester.graphql_query(  # type: ignore[attr-defined]
            query=query, variables=variables
        )

        # Parse response
        try:
            issue_data = result.get("data", {}).get("repository", {}).get("issue")
            if issue_data is None:
                logger.warning(f"Issue #{issue_number} not found")
                return []

            linked_branches = issue_data.get("linkedBranches", {}).get("nodes", [])
            branch_names = [
                node["ref"]["name"]
                for node in linked_branches
                if node and node.get("ref")
            ]
            return branch_names

        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing GraphQL response: {e}")
            return []
