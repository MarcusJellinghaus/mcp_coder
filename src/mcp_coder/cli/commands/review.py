"""Review command implementations (``review-plan`` / ``review-implementation``).

These are thin CLI entry points over :func:`run_review_workflow`. Both verbs
share one ``_execute_review`` helper that resolves arguments exactly like
``execute_implement`` (project/execution dirs, LLM method, MCP config, settings,
issue-interaction flags) and then dispatches to the shared review engine with
the appropriate :class:`ReviewConfig` instance. No ``issue_number`` positional
is accepted; the issue is derived from the current branch inside the workflow.
"""

import argparse
import logging

from ...utils.crash_logging import enable_crash_logging
from ...utils.log_utils import OUTPUT
from ...workflows.review.config import (
    REVIEW_IMPLEMENTATION,
    REVIEW_PLAN,
    ReviewConfig,
)
from ...workflows.review.core import run_review_workflow
from ...workflows.utils import resolve_project_dir
from ..utils import (
    log_command_startup,
    parse_llm_method_from_args,
    resolve_claude_settings_path,
    resolve_execution_dir,
    resolve_issue_interaction_flags,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_review_plan(args: argparse.Namespace) -> int:
    """Execute the ``review-plan`` workflow command.

    Args:
        args: Parsed command line arguments (project/execution dirs, LLM
            method, MCP config, settings, and issue-interaction flags).

    Returns:
        int: Exit code propagated from :func:`run_review_workflow`.
    """
    return _execute_review(args, REVIEW_PLAN)


def execute_review_implementation(args: argparse.Namespace) -> int:
    """Execute the ``review-implementation`` workflow command.

    Args:
        args: Parsed command line arguments (project/execution dirs, LLM
            method, MCP config, settings, and issue-interaction flags).

    Returns:
        int: Exit code propagated from :func:`run_review_workflow`.
    """
    return _execute_review(args, REVIEW_IMPLEMENTATION)


def _execute_review(args: argparse.Namespace, config: ReviewConfig) -> int:
    """Resolve args and run the shared review workflow for ``config``.

    Mirrors ``execute_implement``: resolves the project and execution
    directories, LLM method, MCP config, settings file, and issue-interaction
    flags, then delegates to :func:`run_review_workflow`.

    Args:
        args: Parsed command line arguments.
        config: The static review workflow config (``REVIEW_PLAN`` or
            ``REVIEW_IMPLEMENTATION``).

    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    try:
        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)
        log_command_startup(config.name, project_dir)
        enable_crash_logging(project_dir, config.name)

        # Resolve execution directory
        execution_dir = resolve_execution_dir(args.execution_dir)

        logger.debug(f"Project directory: {project_dir}")
        logger.debug(f"Execution directory: {execution_dir}")

        # Parse LLM method using shared utility
        llm_method, _ = resolve_llm_method(args.llm_method)
        provider = parse_llm_method_from_args(llm_method)

        # Extract and resolve mcp_config / settings paths to absolute paths
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

        # Run the shared review workflow
        return run_review_workflow(
            config,
            project_dir,
            provider,
            mcp_config,
            settings_file,
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
        logger.error(f"Unexpected error in {config.name} command: {e}", exc_info=True)
        return 1
