"""Prerequisites validation for the create_plan workflow.

Functions for validating git state, GitHub issues, branch management,
and pr_info directory setup.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_coder.mcp_workspace_git import checkout_branch
from mcp_coder.utils.github_operations.issues import (
    IssueBranchManager,
    IssueData,
    IssueManager,
)
from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE

# Setup logger
logger = logging.getLogger(__name__)


def check_prerequisites(project_dir: Path, issue_number: int) -> tuple[bool, IssueData]:
    """Validate prerequisites for plan creation workflow.

    Validates that the specified GitHub issue exists and is accessible.

    Note: Git working directory cleanliness is checked by the orchestrator
    in ``run_create_plan_workflow`` before this function runs, so this
    function does not re-check it.

    Args:
        project_dir: Path to the project directory containing git repository
        issue_number: GitHub issue number to validate

    Returns:
        Tuple of (success: bool, issue_data: IssueData)
        - success: True if all prerequisites pass, False otherwise
        - issue_data: IssueData object with issue details, or empty IssueData on failure
    """
    logger.info("Checking prerequisites for plan creation...")

    # Create empty IssueData for failure cases
    empty_issue_data = IssueData(
        number=0,
        title="",
        body="",
        state="",
        labels=[],
        assignees=[],
        user=None,
        created_at=None,
        updated_at=None,
        url="",
        locked=False,
    )

    # Fetch and validate GitHub issue
    try:
        issue_manager = IssueManager(project_dir)
        issue_data = issue_manager.get_issue(issue_number)  # pylint: disable=no-member

        # Check if issue was found (number == 0 indicates not found)
        if issue_data["number"] == 0:
            logger.error(f"✗ Issue #{issue_number} not found or not accessible")
            return (False, empty_issue_data)

        logger.info(f"✓ Issue #{issue_data['number']} exists: '{issue_data['title']}'")

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"✗ Error fetching issue #{issue_number}: {e}")
        return (False, empty_issue_data)

    logger.info("All prerequisites passed")
    return (True, issue_data)


def manage_branch(
    project_dir: Path,
    issue_number: int,
    issue_title: str,  # pylint: disable=unused-argument
    base_branch: Optional[str] = None,
) -> Optional[str]:
    """Get existing linked branch or create new one.

    Args:
        project_dir: Path to the project directory containing git repository
        issue_number: GitHub issue number to link branch to
        issue_title: GitHub issue title for branch name generation
        base_branch: Optional base branch to create from (uses repo default if None)

    Returns:
        Branch name if successful, None on error
    """
    logger.info("Managing branch for issue #%d...", issue_number)

    try:
        # Create IssueBranchManager instance
        manager = IssueBranchManager(project_dir)

        # Get linked branches
        linked_branches = manager.get_linked_branches(issue_number)

        # If linked branches exist, use the first one
        if linked_branches:
            branch_name = linked_branches[0]
            logger.info("Using existing linked branch: %s", branch_name)
        else:
            # Create new branch on GitHub
            result = manager.create_remote_branch_for_issue(
                issue_number,
                base_branch=base_branch,
            )
            if not result["success"]:
                logger.error(
                    "Failed to create branch: %s", result.get("error", "Unknown error")
                )
                return None
            branch_name = result["branch_name"]
            logger.info("Created new branch: %s", branch_name)

        # Checkout the branch locally
        if not checkout_branch(branch_name, project_dir):
            logger.error("Failed to checkout branch: %s", branch_name)
            return None

        logger.info("Switched to branch: %s", branch_name)
        return branch_name

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error("Error managing branch: %s", e)
        return None


def check_pr_info_not_exists(project_dir: Path) -> bool:
    """Check that pr_info/ directory does not exist.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if pr_info/ does not exist, False if it exists
    """
    pr_info_dir = project_dir / "pr_info"

    return not pr_info_dir.exists()


def create_pr_info_structure(project_dir: Path) -> bool:
    """Create pr_info/ directory structure and TASK_TRACKER.md.

    Creates:
    - pr_info/
    - pr_info/steps/
    - pr_info/TASK_TRACKER.md (from template)

    Args:
        project_dir: Path to the project directory

    Returns:
        True if successful, False on error
    """
    try:
        # Build base path
        pr_info_dir = project_dir / "pr_info"

        # Create pr_info/ directory
        pr_info_dir.mkdir(parents=True, exist_ok=False)

        # Create pr_info/steps/ directory
        steps_dir = pr_info_dir / "steps"
        steps_dir.mkdir()

        # Write TASK_TRACKER_TEMPLATE to pr_info/TASK_TRACKER.md
        task_tracker_path = pr_info_dir / "TASK_TRACKER.md"
        task_tracker_path.write_text(TASK_TRACKER_TEMPLATE, encoding="utf-8")

        logger.info("Created pr_info/ directory structure successfully")
        return True

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Failed to create pr_info/ directory structure: {e}")
        return False


def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation.

    Args:
        project_dir_arg: Optional project directory path string, uses current directory if None

    Returns:
        Validated absolute Path to the project directory. Calls sys.exit(1) on validation failure.
    """
    # Use current directory if no argument provided
    if project_dir_arg is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_dir_arg)

    # Resolve to absolute path
    try:
        project_path = project_path.resolve()
    except (OSError, ValueError) as e:
        logger.error(f"Invalid project directory path: {e}")
        sys.exit(1)

    # Validate directory exists
    if not project_path.exists():
        logger.error(f"Project directory does not exist: {project_path}")
        sys.exit(1)

    # Validate it's a directory
    if not project_path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        sys.exit(1)

    # Validate directory is accessible
    try:
        # Test read access by listing directory
        list(project_path.iterdir())
    except PermissionError:
        logger.error(f"No read access to project directory: {project_path}")
        sys.exit(1)

    # Validate directory contains .git subdirectory
    git_dir = project_path / ".git"
    if not git_dir.exists():
        logger.error(f"Project directory is not a git repository: {project_path}")
        sys.exit(1)

    return project_path
