"""CLI commands for GitHub tool operations.

This module provides the gh-tool command group for GitHub-related operations.
"""

import argparse
import logging
import sys

from ...utils.git_operations.branches import checkout_branch
from ...utils.git_operations.remotes import fetch_remote
from ...utils.github_operations.issues.branch_manager import IssueBranchManager
from ...utils.github_operations.issues.manager import IssueManager
from ...workflow_utils.base_branch import detect_base_branch
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)


def execute_get_base_branch(args: argparse.Namespace) -> int:
    """Execute get-base-branch command.

    Detection priority:
    1. GitHub PR base branch (if open PR exists)
    2. Linked issue's ### Base Branch section
    3. Default branch (main/master)

    Args:
        args: Parsed arguments with project_dir option

    Returns:
        0: Success, branch name printed to stdout
        1: Could not detect base branch
        2: Error (not a git repo, API failure)
    """
    try:
        logger.info("Starting get-base-branch detection")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Use the shared detect_base_branch function
        base_branch = detect_base_branch(project_dir)

        if base_branch == "unknown":
            logger.warning("Could not detect base branch from PR, issue, or default")
            return 1

        print(base_branch)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Error detecting base branch: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2


def execute_checkout_issue_branch(args: argparse.Namespace) -> int:
    """Execute checkout-issue-branch command.

    Fetches issue data, finds or creates a linked branch, and checks it out locally.

    Args:
        args: Parsed arguments with issue_number and project_dir option

    Returns:
        0: Success, branch checked out
        1: Could not find or create branch
        2: Error (not a git repo, API failure, git checkout failure)
    """
    try:
        logger.info("Starting checkout-issue-branch")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Best-effort git fetch
        if not fetch_remote(project_dir):
            logger.debug("git fetch failed (continuing)")

        # Get issue data
        issue_number: int = args.issue_number
        issue_data = IssueManager(project_dir).get_issue(issue_number)

        if issue_data["number"] == 0:
            print(
                f"Error: Could not find issue #{issue_number}",
                file=sys.stderr,
            )
            return 1

        # Find or create linked branch
        branch_manager = IssueBranchManager(project_dir)
        branches = branch_manager.get_linked_branches(issue_number)

        if branches:
            branch_name = branches[0]
        else:
            result = branch_manager.create_remote_branch_for_issue(
                issue_number, base_branch=issue_data.get("base_branch")
            )
            if not result["success"]:
                print(
                    f"Error: Could not create branch for issue #{issue_number}: {result['error']}",
                    file=sys.stderr,
                )
                return 1
            branch_name = result["branch_name"]

        # Checkout the branch
        if not checkout_branch(branch_name, project_dir):
            logger.error(f"Git checkout failed for branch '{branch_name}'")
            print(
                f"Error: git checkout failed for branch '{branch_name}'",
                file=sys.stderr,
            )
            return 2

        print(branch_name)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Error during checkout-issue-branch: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2
