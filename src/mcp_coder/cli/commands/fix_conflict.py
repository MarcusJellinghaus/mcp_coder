"""Fix-conflict command implementation.

This module provides the CLI command interface for the fix-conflict
workflow, which rebases a PR with a detected merge conflict - git-only
first, then the LLM rebase on conflict - (dispatched from
``status-71:merge-conflict`` via Jenkins).
"""

import argparse
import logging

from ...utils.crash_logging import enable_crash_logging
from ...utils.log_utils import OUTPUT
from ...workflows.utils import resolve_project_dir
from ..utils import (
    log_command_startup,
    parse_llm_method_from_args,
    resolve_auto_merge,
    resolve_claude_settings_path,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_fix_conflict(args: argparse.Namespace) -> int:
    """Execute the fix-conflict workflow command.

    Args:
        args: Parsed arguments with `project_dir`, `llm_method`, `mcp_config`,
            `settings` and `auto_merge`. Without `--settings` the LLM rebase
            uses the least-privilege rebase settings (no `settings.local.json`
            auto-detection).

    Returns:
        int: exit code from run_fix_conflict_workflow (0/1), or 1 on a
        resolution/argument/keyboard-interrupt error at the CLI boundary.
    """
    try:
        project_dir = resolve_project_dir(args.project_dir)
        log_command_startup("fix-conflict", project_dir)
        enable_crash_logging(project_dir, "fix-conflict")
        auto_merge = resolve_auto_merge(args, project_dir)

        llm_method, _ = resolve_llm_method(args.llm_method)
        provider = parse_llm_method_from_args(llm_method)
        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )
        settings = (
            resolve_claude_settings_path(args.settings, project_dir=args.project_dir)
            if args.settings
            else None
        )

        # Import here to avoid circular dependency during module load
        from ...workflows.fix_conflict.core import run_fix_conflict_workflow

        return run_fix_conflict_workflow(
            project_dir, provider, mcp_config, settings, auto_merge=auto_merge
        )

    except ValueError as e:
        logger.error(f"Invalid project directory: {e}")
        return 1

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except Exception as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in fix-conflict command: {e}", exc_info=True)
        return 1
