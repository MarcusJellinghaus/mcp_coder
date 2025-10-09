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
    # Step 1: Protect " - " separator with placeholder (GitHub-specific rule)
    # Use lowercase placeholder to avoid case conversion issues
    PROTECTED_SEPARATOR = "\x00sep\x00"
    sanitized = issue_title.replace(" - ", PROTECTED_SEPARATOR)

    # Step 2: Convert to lowercase
    sanitized = sanitized.lower()

    # Step 3: Replace non-alphanumeric (except dash and placeholder) with dash
    sanitized = re.sub(r"[^a-z0-9-\x00]+", "-", sanitized)

    # Step 4: Collapse multiple consecutive dashes to single dash
    sanitized = re.sub(r"-{2,}", "-", sanitized)

    # Step 5: Restore protected separators as "---"
    sanitized = sanitized.replace(PROTECTED_SEPARATOR, "---")

    # Step 6: Strip leading/trailing dashes
    sanitized = sanitized.strip("-")

    # Step 7: Truncate to max_length if needed
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

    @log_function_call
    @_handle_github_errors(
        default_return=BranchCreationResult(
            success=False, branch_name="", error=None, existing_branches=[]
        )
    )
    def create_remote_branch_for_issue(
        self,
        issue_number: int,
        branch_name: Optional[str] = None,
        base_branch: Optional[str] = None,
        allow_multiple: bool = False,
    ) -> BranchCreationResult:
        """Create and link branch to issue via GraphQL.

        Args:
            issue_number: Issue number to link branch to
            branch_name: Custom branch name (optional, auto-generated if not provided)
            base_branch: Base branch to branch from (optional, uses default branch if not provided)
            allow_multiple: If False (default), blocks if issue has any linked branches.
                           If True, allows multiple branches per issue.

        Returns:
            BranchCreationResult with success status, branch name, error, and existing branches

        Example:
            >>> manager = IssueBranchManager(Path.cwd())
            >>> result = manager.create_remote_branch_for_issue(123)
            >>> if result["success"]:
            ...     print(f"Created branch: {result['branch_name']}")
            ... else:
            ...     print(f"Error: {result['error']}")
        """
        # Validate issue number
        if not self._validate_issue_number(issue_number):
            return BranchCreationResult(
                success=False,
                branch_name="",
                error="Invalid issue number. Must be a positive integer.",
                existing_branches=[],
            )

        # Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return BranchCreationResult(
                success=False,
                branch_name="",
                error="Failed to get repository",
                existing_branches=[],
            )

        # Step 1: Check for existing branches if allow_multiple=False
        if not allow_multiple:
            existing_branches = self.get_linked_branches(issue_number)
            if existing_branches:
                error_msg = (
                    f"Issue #{issue_number} already has linked branches. "
                    f"Use allow_multiple=True to create additional branches."
                )
                logger.warning(error_msg)
                return BranchCreationResult(
                    success=False,
                    branch_name="",
                    error=error_msg,
                    existing_branches=existing_branches,
                )

        # Step 2: Get issue to access node_id and title
        issue = repo.get_issue(issue_number)

        # Step 3: Generate branch name if not provided
        if branch_name is None:
            branch_name = generate_branch_name_from_issue(issue_number, issue.title)

        # Step 4: Get base commit SHA
        base_branch_name = base_branch if base_branch else repo.default_branch
        branch = repo.get_branch(base_branch_name)
        base_commit_sha = branch.commit.sha

        # Step 5: Execute createLinkedBranch mutation
        mutation_input = {
            "issueId": issue.node_id,
            "repositoryId": repo.node_id,
            "oid": base_commit_sha,
            "name": branch_name,
        }

        # Execute GraphQL mutation
        # Note: Using private attribute is the documented way to access GraphQL in PyGithub
        result = self._github_client._Github__requester.graphql_named_mutation(  # type: ignore[attr-defined]
            mutation_name="createLinkedBranch",
            mutation_input=mutation_input,
            output_schema="linkedBranch { id ref { name target { oid } } }",
        )

        # Step 6: Parse response and return result
        try:
            data = result.get("data")
            if data is None:
                error_msg = "Failed to create linked branch: Invalid response from GitHub (null data)"
                logger.error(error_msg)
                return BranchCreationResult(
                    success=False,
                    branch_name="",
                    error=error_msg,
                    existing_branches=[],
                )

            linked_branch_data = data.get("createLinkedBranch")
            if (
                linked_branch_data is None
                or linked_branch_data.get("linkedBranch") is None
            ):
                error_msg = (
                    "Failed to create linked branch: Invalid response from GitHub"
                )
                logger.error(error_msg)
                return BranchCreationResult(
                    success=False,
                    branch_name="",
                    error=error_msg,
                    existing_branches=[],
                )

            created_branch = linked_branch_data["linkedBranch"]
            created_branch_name = created_branch["ref"]["name"]

            logger.info(
                f"Successfully created and linked branch '{created_branch_name}' to issue #{issue_number}"
            )
            return BranchCreationResult(
                success=True,
                branch_name=created_branch_name,
                error=None,
                existing_branches=[],
            )

        except (KeyError, TypeError) as e:
            error_msg = f"Error parsing GraphQL mutation response: {e}"
            logger.error(error_msg)
            return BranchCreationResult(
                success=False,
                branch_name="",
                error=error_msg,
                existing_branches=[],
            )

    @log_function_call
    @_handle_github_errors(default_return=False)
    def delete_linked_branch(self, issue_number: int, branch_name: str) -> bool:
        """Unlink branch from issue (doesn't delete Git branch).

        Args:
            issue_number: Issue number to unlink branch from
            branch_name: Name of the branch to unlink

        Returns:
            True if successfully unlinked, False otherwise

        Example:
            >>> manager = IssueBranchManager(Path.cwd())
            >>> success = manager.delete_linked_branch(123, "123-feature-branch")
            >>> if success:
            ...     print("Branch unlinked successfully")
            ... else:
            ...     print("Failed to unlink branch")
        """
        # Step 1: Validate inputs
        if not self._validate_issue_number(issue_number):
            return False

        if not branch_name or not branch_name.strip():
            logger.error("Branch name cannot be empty")
            return False

        # Step 2: Get repository
        repo = self._get_repository()
        if repo is None:
            logger.error("Failed to get repository")
            return False

        # Extract owner and repo name
        owner, repo_name = repo.owner.login, repo.name

        # Step 3: Query linked branches to get linkedBranch.id
        query = """
        query($owner: String!, $repo: String!, $issueNumber: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $issueNumber) {
              linkedBranches(first: 100) {
                nodes {
                  id
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
        result = self._github_client._Github__requester.graphql_query(  # type: ignore[attr-defined]
            query=query, variables=variables
        )

        # Step 4: Find matching branch by name and extract its ID
        try:
            issue_data = result.get("data", {}).get("repository", {}).get("issue")
            if issue_data is None:
                logger.warning(f"Issue #{issue_number} not found")
                return False

            linked_branches = issue_data.get("linkedBranches", {}).get("nodes", [])

            # Find the branch with matching name
            linked_branch_id = None
            for node in linked_branches:
                if node and node.get("ref") and node["ref"].get("name") == branch_name:
                    linked_branch_id = node.get("id")
                    break

            # Step 5: If not found, log warning and return False
            if linked_branch_id is None:
                logger.warning(
                    f"Branch '{branch_name}' is not linked to issue #{issue_number}"
                )
                return False

            # Step 6: Execute deleteLinkedBranch mutation
            mutation_input = {"linkedBranchId": linked_branch_id}

            self._github_client._Github__requester.graphql_named_mutation(  # type: ignore[attr-defined]
                mutation_name="deleteLinkedBranch",
                mutation_input=mutation_input,
                output_schema="clientMutationId",
            )

            logger.info(
                f"Successfully unlinked branch '{branch_name}' from issue #{issue_number}"
            )
            return True

        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing GraphQL response: {e}")
            return False
