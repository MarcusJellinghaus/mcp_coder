"""Create plan command implementation.

This module provides the CLI command interface for the create-plan workflow,
which generates implementation plans for GitHub issues.
"""

import argparse
import logging
import sys

from ...workflows.utils import resolve_project_dir
from ..utils import (
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_create_plan(args: argparse.Namespace) -> int:
    """Execute the create-plan workflow command.

    Args:
        args: Parsed command line arguments with:
            - issue_number: GitHub issue number (int)
            - project_dir: Optional project directory path
            - execution_dir: Optional execution directory (NEW)
            - llm_method: LLM method to use ('claude' or 'langchain')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting create-plan command execution")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Resolve execution directory
        execution_dir = resolve_execution_dir(args.execution_dir)

        # Log both directories for clarity
        logger.debug(f"Project directory: {project_dir}")
        logger.debug(f"Execution directory: {execution_dir}")

        # Parse LLM method using shared utility
        llm_method, _ = resolve_llm_method(args.llm_method)
        provider = parse_llm_method_from_args(llm_method)

        # Extract and resolve mcp_config path to absolute path
        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )

        # Extract update_labels flag from args
        update_labels = getattr(args, "update_labels", False)

        # Import here to avoid circular dependency during module load
        from ...workflows.create_plan import run_create_plan_workflow

        # Run the create-plan workflow
        return run_create_plan_workflow(
            args.issue_number,
            project_dir,
            provider,
            mcp_config,
            execution_dir,
            update_labels,
        )

    except ValueError as e:
        # Handle invalid execution_dir
        logger.error(f"Invalid execution directory: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1

    except Exception as e:
        print(f"Error during workflow execution: {e}", file=sys.stderr)
        logger.error(f"Unexpected error in create-plan command: {e}", exc_info=True)
        return 1
