"""CLI commands for Git tool operations.

This module provides the git-tool command group for Git-related operations.
"""

import argparse
import logging
import sys

from ...utils.git_operations.compact_diffs import get_compact_diff
from ...utils.git_operations.diffs import get_git_diff_for_commit
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

        # Get committed changes
        committed_diff = get_compact_diff(project_dir, base_branch, args.exclude or [])

        # Get uncommitted changes (unless --committed-only flag set)
        if not args.committed_only:
            uncommitted_diff = get_git_diff_for_commit(project_dir)

            if uncommitted_diff:
                if committed_diff:
                    result = f"{committed_diff}\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
                else:
                    result = f"No committed changes\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
            else:
                result = committed_diff
        else:
            result = committed_diff

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
