"""Create PR command implementation.

This module provides the CLI command interface for the create-pr workflow,
which generates PR summaries and cleans up repository state.
"""

import argparse
import logging
import sys
from pathlib import Path

from ...workflows.create_pr.core import run_create_pr_workflow
from ...workflows.utils import resolve_project_dir
from ..utils import parse_llm_method_from_args

logger = logging.getLogger(__name__)


def execute_create_pr(args: argparse.Namespace) -> int:
    """Execute the create-pr workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude_code_cli' or 'claude_code_api')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting create-pr command execution")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Parse LLM method using shared utility
        provider, method = parse_llm_method_from_args(args.llm_method)

        # Run the create-pr workflow
        return run_create_pr_workflow(project_dir, provider, method)

    except KeyboardInterrupt:
        print("Operation cancelled by user.")
        return 1

    except Exception as e:
        print(f"Error during workflow execution: {e}", file=sys.stderr)
        logger.error(f"Unexpected error in create-pr command: {e}", exc_info=True)
        return 1
