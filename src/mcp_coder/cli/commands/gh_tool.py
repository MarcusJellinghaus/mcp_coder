"""CLI commands for GitHub tool operations.

This module provides the gh-tool command group for GitHub-related operations.
"""

import argparse
import logging
import sys

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
    except Exception as e:
        logger.error(f"Error detecting base branch: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2
