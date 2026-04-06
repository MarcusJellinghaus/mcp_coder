"""Create PR command implementation.

This module provides the CLI command interface for the create-pr workflow,
which generates PR summaries and cleans up repository state.
"""

import argparse
import logging

from ...utils.log_utils import OUTPUT
from ...workflows.create_pr.core import run_create_pr_workflow
from ...workflows.utils import resolve_project_dir
from ..utils import (
    log_command_startup,
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_issue_interaction_flags,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_create_pr(args: argparse.Namespace) -> int:
    """Execute the create-pr workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - execution_dir: Optional execution directory (NEW)
            - llm_method: LLM method to use ('claude' or 'langchain')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)
        log_command_startup("create-pr", project_dir)

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

        # Resolve issue interaction flags (CLI > config > default)
        update_issue_labels, post_issue_comments = resolve_issue_interaction_flags(
            args, project_dir
        )

        # Run the create-pr workflow
        return run_create_pr_workflow(
            project_dir,
            provider,
            mcp_config,
            execution_dir,
            update_issue_labels,
            post_issue_comments,
        )

    except ValueError as e:
        # Handle invalid execution_dir
        logger.error(f"Invalid execution directory: {e}")
        return 1

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in create-pr command: {e}", exc_info=True)
        return 1
