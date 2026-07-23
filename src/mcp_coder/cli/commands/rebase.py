"""Rebase command implementation.

This module provides the CLI command interface for the automated rebase
workflow, which rebases the current feature branch onto its base branch,
resolves conflicts + verifies via a single LLM session, and force-pushes with
``--force-with-lease``.

Exit-code contract (see ``workflows/rebase.py`` / ``pr_info`` summary):
    0 = success or no-op, 1 = aborted (needs human), 2 = error / push rejected.
"""

import argparse
import json
import logging
import tempfile

from ...utils.log_utils import OUTPUT
from ...workflows.rebase_permissions import REBASE_LLM_PERMISSIONS
from ...workflows.utils import resolve_project_dir
from ..utils import (
    parse_llm_method_from_args,
    resolve_claude_settings_path,
    resolve_execution_dir,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def _resolve_rebase_settings(settings_arg: str | None, project_dir: str | None) -> str:
    """Resolve the Claude settings file for the rebase LLM session.

    When ``--settings`` is provided explicitly, delegate to the standard
    resolver. Otherwise materialize the least-privilege ``REBASE_LLM_PERMISSIONS``
    constant to a runtime temp JSON file and return its path, bypassing the broad
    ``settings.local.json`` auto-detect. The temp file lives for the duration of
    the process/session.

    Args:
        settings_arg: Explicit ``--settings`` path, or None.
        project_dir: Project directory used as the base for relative paths.

    Returns:
        Absolute path to the settings file to pass as ``settings_file``.
    """
    if settings_arg is not None:
        resolved = resolve_claude_settings_path(settings_arg, project_dir=project_dir)
        # Explicit paths are strict: the resolver returns a str or raises.
        assert resolved is not None  # nosec B101
        return resolved

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(REBASE_LLM_PERMISSIONS, handle)
        temp_path = handle.name
    logger.debug("Materialized least-privilege rebase settings to %s", temp_path)
    return temp_path


def execute_rebase(args: argparse.Namespace) -> int:
    """Execute the automated rebase workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - execution_dir: Optional execution directory
            - llm_method: LLM method to use ('claude' or 'langchain')
            - mcp_config: Optional MCP config path
            - settings: Optional Claude settings path
            - base_branch: Optional explicit base branch

    Returns:
        int: Exit code (0 success/no-op, 1 aborted, 2 error). Caught boundary
        errors (invalid args, unexpected exceptions) return 1.
    """
    try:
        project_dir = resolve_project_dir(args.project_dir)
        execution_dir = resolve_execution_dir(args.execution_dir)

        logger.debug("Project directory: %s", project_dir)
        logger.debug("Execution directory: %s", execution_dir)

        llm_method, _ = resolve_llm_method(args.llm_method)
        provider = parse_llm_method_from_args(llm_method)

        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )
        settings_file = _resolve_rebase_settings(args.settings, args.project_dir)

        # Import here to avoid circular dependency during module load
        from ...workflows.rebase import run_rebase_workflow

        return run_rebase_workflow(
            project_dir,
            provider,
            args.base_branch,
            mcp_config,
            settings_file,
            execution_dir,
        )

    except ValueError as e:
        logger.error(f"Invalid execution directory: {e}")
        return 1

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in rebase command: {e}", exc_info=True)
        return 1
