"""Implement command implementation.

This module provides the CLI command interface for the implement workflow,
which processes implementation tasks from the task tracker.
"""

import argparse
import logging
import sys
from pathlib import Path

from ...workflows.implement.core import resolve_project_dir, run_implement_workflow

logger = logging.getLogger(__name__)


def execute_implement(args: argparse.Namespace) -> int:
    """Execute the implement workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude_code_cli' or 'claude_code_api')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting implement command execution")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Run the implement workflow
        return run_implement_workflow(project_dir, args.llm_method)

    except KeyboardInterrupt:
        print("Operation cancelled by user.")
        return 1

    except Exception as e:
        print(f"Error during workflow execution: {e}", file=sys.stderr)
        logger.error(f"Unexpected error in implement command: {e}", exc_info=True)
        return 1
