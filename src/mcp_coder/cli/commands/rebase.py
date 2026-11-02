"""Rebase command implementation.

This module provides the CLI command interface for the automated rebase
workflow, which rebases the current feature branch onto its base branch,
resolves conflicts + verifies via a single LLM session, and force-pushes with
``--force-with-lease``.

Exit-code contract (see ``workflows/rebase.py`` / ``pr_info`` summary):
    0 = success or no-op, 1 = aborted (needs human), 2 = error / push rejected.
"""

import argparse
import logging

from ...utils.log_utils import OUTPUT
from ...workflows.rebase_permissions import rebase_settings_file
from ...workflows.utils import resolve_project_dir
from ..utils import (
    parse_llm_method_from_args,
    resolve_claude_cwd,
    resolve_claude_settings_path,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def _resolve_rebase_settings(
    settings_arg: str | None, project_dir: str | None
) -> str | None:
    """Resolve an explicit ``--settings`` path for the rebase LLM session.

    When ``--settings`` is provided explicitly, delegate to the standard
    resolver. Otherwise return None so ``rebase_settings_file`` materializes the
    least-privilege ``REBASE_LLM_PERMISSIONS``, bypassing the broad
    ``settings.local.json`` auto-detect.

    Args:
        settings_arg: Explicit ``--settings`` path, or None.
        project_dir: Project directory used as the base for relative paths.

    Returns:
        Absolute path to the explicit settings file, or None.
    """
    if settings_arg is None:
        return None
    resolved = resolve_claude_settings_path(settings_arg, project_dir=project_dir)
    # Explicit paths are strict: the resolver returns a str or raises.
    assert resolved is not None  # noqa: S101  # nosec B101
    return resolved


def execute_rebase(args: argparse.Namespace) -> int:
    """Execute the automated rebase workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude' or 'langchain')
            - mcp_config: Optional MCP config path
            - settings: Optional Claude settings path
            - base_branch: Optional explicit base branch

    Returns:
        int: Exit code (0 success/no-op, 1 aborted, 2 error). Caught boundary
        errors (invalid args, unexpected exceptions) return 2 — no LLM ran, so
        they are errors, not a needs-human abort.
    """
    try:
        project_dir = resolve_project_dir(args.project_dir)
        project_dir = resolve_claude_cwd(project_dir)

        logger.debug("Project directory: %s", project_dir)

        llm_method, _ = resolve_llm_method(args.llm_method)
        provider = parse_llm_method_from_args(llm_method)

        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )
        explicit_settings = _resolve_rebase_settings(args.settings, args.project_dir)

        # Import here to avoid circular dependency during module load
        from ...workflows.rebase import run_rebase_workflow

        with rebase_settings_file(explicit_settings) as settings_file:
            return run_rebase_workflow(
                project_dir,
                provider,
                args.base_branch,
                mcp_config,
                settings_file,
            ).exit_code

    except ValueError as e:
        logger.error(f"Invalid project directory: {e}")
        return 2

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except Exception as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in rebase command: {e}", exc_info=True)
        return 2
