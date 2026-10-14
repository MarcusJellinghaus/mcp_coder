"""Fix-ci command implementation.

This module provides the CLI command interface for the fix-ci workflow,
which reuses the CI auto-fix loop to try to resolve a failing PR's CI
(dispatched from ``status-82:fixing-ci`` via Jenkins).
"""

import argparse
import logging

from ...utils.crash_logging import enable_crash_logging
from ...utils.log_utils import OUTPUT
from ...workflows.fix_ci.core import run_fix_ci_workflow
from ...workflows.utils import resolve_project_dir
from ..utils import (
    log_command_startup,
    parse_llm_method_from_args,
    resolve_claude_cwd,
    resolve_claude_settings_path,
    resolve_issue_interaction_flags,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_fix_ci(args: argparse.Namespace) -> int:
    """Execute the fix-ci workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude' or 'langchain')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)
        log_command_startup("fix-ci", project_dir)
        enable_crash_logging(project_dir, "fix-ci")

        # Resolve the working directory for the Claude subprocess
        project_dir = resolve_claude_cwd(project_dir)

        logger.debug(f"Project directory: {project_dir}")

        # Parse LLM method using shared utility
        llm_method, _ = resolve_llm_method(args.llm_method)
        provider = parse_llm_method_from_args(llm_method)

        # Extract and resolve mcp_config path to absolute path
        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )
        settings_file = resolve_claude_settings_path(
            args.settings, project_dir=args.project_dir
        )

        # Resolve issue interaction flags (CLI > config > default)
        update_issue_labels, post_issue_comments = resolve_issue_interaction_flags(
            args, project_dir
        )

        # Run the fix-ci workflow
        return run_fix_ci_workflow(
            project_dir,
            provider,
            mcp_config,
            settings_file,
            update_issue_labels,
            post_issue_comments,
        )

    except ValueError as e:
        logger.error(f"Invalid project directory: {e}")
        return 1

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in fix-ci command: {e}", exc_info=True)
        return 1
