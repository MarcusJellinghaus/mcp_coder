"""Fix-conflict command implementation.

This module provides the CLI command interface for the fix-conflict
workflow, which performs the mechanical rebase that resolves a detected
merge conflict on a PR (dispatched from ``status-71:merge-conflict`` via
Jenkins).
"""

import argparse
import logging

from ...utils.crash_logging import enable_crash_logging
from ...utils.log_utils import OUTPUT
from ...workflows.utils import resolve_project_dir
from ..utils import log_command_startup

logger = logging.getLogger(__name__)


def execute_fix_conflict(args: argparse.Namespace) -> int:
    """Execute the fix-conflict workflow command.

    Args:
        args: Parsed arguments with `project_dir`.

    Returns:
        int: exit code from run_fix_conflict_workflow (0/1), or 1 on a
        resolution/argument/keyboard-interrupt error at the CLI boundary.
    """
    try:
        project_dir = resolve_project_dir(args.project_dir)
        log_command_startup("fix-conflict", project_dir)
        enable_crash_logging(project_dir, "fix-conflict")

        # Import here to avoid circular dependency during module load
        from ...workflows.fix_conflict.core import run_fix_conflict_workflow

        return run_fix_conflict_workflow(project_dir)

    except ValueError as e:
        logger.error(f"Invalid project directory: {e}")
        return 1

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in fix-conflict command: {e}", exc_info=True)
        return 1
