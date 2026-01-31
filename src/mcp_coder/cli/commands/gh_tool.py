"""CLI commands for GitHub tool operations.

This module provides the gh-tool command group for GitHub-related operations.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from ...utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
)
from ...utils.github_operations.issue_manager import IssueManager
from ...utils.github_operations.pr_manager import PullRequestManager
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

        # Get current branch name
        current_branch = get_current_branch_name(project_dir)
        logger.debug(f"Current branch: {current_branch}")

        # Try PR detection first (highest priority)
        base_branch = _detect_from_pr(project_dir, current_branch)
        if base_branch:
            print(base_branch)
            return 0

        # Try issue detection (second priority)
        base_branch = _detect_from_issue(project_dir, current_branch)
        if base_branch:
            print(base_branch)
            return 0

        # Fallback to default branch
        base_branch = _detect_default_branch(project_dir)
        if base_branch:
            print(base_branch)
            return 0

        # All detection methods failed
        logger.warning("Could not detect base branch from PR, issue, or default")
        return 1

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        logger.error(f"Error detecting base branch: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2


def _detect_from_pr(project_dir: Path, current_branch: Optional[str]) -> Optional[str]:
    """Detect base branch from open PR.

    Args:
        project_dir: Project directory path
        current_branch: Current branch name (can be None for detached HEAD)

    Returns:
        Base branch name if PR found, None otherwise
    """
    if current_branch is None:
        logger.debug("No current branch (detached HEAD), skipping PR detection")
        return None

    try:
        pr_manager = PullRequestManager(project_dir)
        open_prs = pr_manager.list_pull_requests(state="open")

        for pr in open_prs:
            if pr.get("head_branch") == current_branch:
                base_branch = pr.get("base_branch")
                logger.info(f"Found base branch from PR: {base_branch}")
                return base_branch

        logger.debug(f"No open PR found for branch '{current_branch}'")
        return None

    except Exception as e:
        logger.debug(f"PR detection failed: {e}")
        return None


def _detect_from_issue(
    project_dir: Path, current_branch: Optional[str]
) -> Optional[str]:
    """Detect base branch from linked issue.

    Args:
        project_dir: Project directory path
        current_branch: Current branch name (can be None for detached HEAD)

    Returns:
        Base branch name if issue has base_branch, None otherwise
    """
    if current_branch is None:
        logger.debug("No current branch (detached HEAD), skipping issue detection")
        return None

    # Extract issue number from branch name
    issue_number = extract_issue_number_from_branch(current_branch)
    if issue_number is None:
        logger.debug(f"No issue number in branch name '{current_branch}'")
        return None

    try:
        issue_manager = IssueManager(project_dir=project_dir)
        issue_data = issue_manager.get_issue(issue_number)

        # Check if issue was found (number=0 indicates not found)
        if issue_data.get("number", 0) == 0:
            logger.debug(f"Issue #{issue_number} not found")
            return None

        base_branch = issue_data.get("base_branch")
        if base_branch:
            logger.info(f"Found base branch from issue #{issue_number}: {base_branch}")
            return base_branch

        logger.debug(f"Issue #{issue_number} has no base_branch specified")
        return None

    except Exception as e:
        logger.debug(f"Issue detection failed: {e}")
        return None


def _detect_default_branch(project_dir: Path) -> Optional[str]:
    """Detect default branch (main/master).

    Args:
        project_dir: Project directory path

    Returns:
        Default branch name if found, None otherwise
    """
    try:
        default_branch = get_default_branch_name(project_dir)
        if default_branch:
            logger.info(f"Using default branch: {default_branch}")
            return default_branch

        logger.debug("Could not determine default branch")
        return None

    except Exception as e:
        logger.debug(f"Default branch detection failed: {e}")
        return None
