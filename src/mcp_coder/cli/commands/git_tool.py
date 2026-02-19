"""CLI commands for Git tool operations.

This module provides the git-tool command group for Git-related operations.
"""

import argparse
import logging
import sys

from ...utils.git_operations.compact_diffs import get_compact_diff
from ...workflow_utils.base_branch import detect_base_branch
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)


def execute_compact_diff(args: argparse.Namespace) -> int:
    """Execute git-tool compact-diff command.

    Returns:
        0  Success — compact diff printed to stdout
        1  Could not detect base branch
        2  Error (invalid repo, unexpected exception)
    """
    try:
        logger.info("Starting compact-diff")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Use provided base branch or auto-detect
        base_branch = (
            args.base_branch if args.base_branch else detect_base_branch(project_dir)
        )

        if base_branch is None:
            logger.warning("Could not detect base branch")
            print("Error: Could not detect base branch", file=sys.stderr)
            return 1

        result = get_compact_diff(project_dir, base_branch, args.exclude or [])
        print(result)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        logger.error(f"Error generating compact diff: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2
