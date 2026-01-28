"""CLI command for checking branch status and optionally running auto-fixes.

This module provides the check-branch-status command that collects comprehensive
branch status information and can automatically fix CI failures when requested.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from ...utils.git_operations.readers import get_current_branch_name
from ...workflow_utils.branch_status import BranchStatusReport, collect_branch_status
from ...workflows.implement.core import check_and_fix_ci
from ...workflows.utils import resolve_project_dir
from ..utils import (
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_check_branch_status(args: argparse.Namespace) -> int:
    """Execute branch status check command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - fix: Whether to attempt automatic fixes
            - llm_truncate: Whether to use LLM-friendly output format
            - llm_method: LLM method for fixes (if --fix enabled)
            - mcp_config: Optional MCP configuration path
            - execution_dir: Optional execution directory

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting branch status check")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Collect branch status
        logger.debug("Collecting branch status information")
        report = collect_branch_status(project_dir, args.llm_truncate)

        # Display status report
        # Use errors='replace' to handle emoji encoding issues on Windows
        output = (
            report.format_for_llm() if args.llm_truncate else report.format_for_human()
        )
        try:
            print(output)
        except UnicodeEncodeError:
            # Fallback for terminals that can't display Unicode
            print(output.encode("ascii", errors="replace").decode("ascii"))

        # Run auto-fixes if requested
        if args.fix:
            logger.info("Auto-fix mode enabled")

            # Parse LLM method for fixes
            provider, method = parse_llm_method_from_args(args.llm_method)

            # Resolve paths for fix operations
            mcp_config = resolve_mcp_config_path(args.mcp_config)
            execution_dir = resolve_execution_dir(args.execution_dir)

            # Attempt fixes
            fix_success = _run_auto_fixes(
                project_dir, report, provider, method, mcp_config, execution_dir
            )

            if not fix_success:
                logger.error("Auto-fix operations failed")
                return 1

            logger.info("Auto-fix operations completed successfully")

        return 0

    except Exception as e:
        print(f"Error collecting branch status: {e}", file=sys.stderr)
        logger.error(
            f"Unexpected error in check_branch_status command: {e}", exc_info=True
        )
        return 1


def _run_auto_fixes(
    project_dir: Path,
    report: BranchStatusReport,
    provider: str,
    method: str,
    mcp_config: Optional[str],
    execution_dir: Optional[Path],
) -> bool:
    """Attempt automatic fixes based on status report.

    Args:
        project_dir: Project directory path
        report: Branch status report
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'api')
        mcp_config: Optional MCP configuration path
        execution_dir: Optional execution directory

    Returns:
        True if all applicable fixes succeeded, False if any fix failed
    """
    logger.debug("Analyzing status report for auto-fixable issues")

    # Only auto-fix CI failures - other issues are informational only
    if report.ci_status == "FAILED":
        logger.info("CI failures detected - attempting automatic fixes")

        try:
            # Use existing CI fix logic from implement workflow
            # Get current branch from project directory
            current_branch = get_current_branch_name(project_dir)
            if not current_branch:
                logger.error("Could not determine current branch name")
                return False

            # Call CI fix function
            ci_success = check_and_fix_ci(
                project_dir, current_branch, provider, method, mcp_config, execution_dir
            )

            if ci_success:
                logger.info("CI fixes completed successfully")
                return True
            else:
                logger.error("CI fixes failed")
                return False

        except Exception as e:
            logger.error(f"Exception during CI fix: {e}")
            return False

    else:
        logger.info(
            "No auto-fixable issues found - all fixes require manual intervention"
        )
        logger.info(
            "Rebase operations, task completion, and GitHub label updates must be done manually"
        )
        return True  # Success when no fixes needed
