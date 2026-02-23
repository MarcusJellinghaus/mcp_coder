"""CLI command for checking branch status and optionally running auto-fixes.

This module provides the check-branch-status command that collects comprehensive
branch status information and can automatically fix CI failures when requested.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from ...checks.branch_status import BranchStatusReport, collect_branch_status
from ...utils.git_operations.readers import get_current_branch_name
from ...utils.github_operations.ci_results_manager import (
    CIResultsManager,
    CIStatusData,
)
from ...workflows.implement.core import check_and_fix_ci
from ...workflows.utils import resolve_project_dir
from ..utils import (
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def _show_progress(show: bool) -> None:
    """Print a progress dot if show is True.

    Args:
        show: Whether to show progress (False in LLM mode)
    """
    if not show:
        return
    print(".", end="", flush=True)


def _wait_for_ci_completion(
    ci_manager: CIResultsManager,
    branch: str,
    timeout_seconds: int,
    llm_mode: bool,
) -> Tuple[Optional[CIStatusData], bool]:
    """Wait for CI completion with timeout.

    Args:
        ci_manager: CI results manager instance
        branch: Branch name to check
        timeout_seconds: Maximum seconds to wait
        llm_mode: True to suppress progress output

    Returns:
        Tuple of (ci_status, success):
        - ci_status: Latest CI status dict or None
        - success: True if CI passed, False if failed/timeout
    """
    if timeout_seconds <= 0:
        return None, True  # Graceful exit, no wait requested

    show_progress = not llm_mode
    poll_interval = 15  # seconds
    max_attempts = timeout_seconds // poll_interval

    if show_progress:
        print(f"Waiting for CI completion (timeout: {timeout_seconds}s)...", end="")

    for attempt in range(max_attempts):
        try:
            ci_status = ci_manager.get_latest_ci_status(branch)
        except Exception as e:
            logger.error(f"CI API error during polling: {e}")
            if show_progress:
                print()  # Newline after dots
            return None, False  # Technical error on API errors

        run_info = ci_status.get("run", {})

        # No CI run found yet
        if not run_info:
            if attempt == max_attempts - 1:
                if show_progress:
                    print()
                logger.info("No CI run found within timeout")
                return None, True  # Graceful exit
            _show_progress(show_progress)
            time.sleep(poll_interval)
            continue

        # Check if CI completed
        if run_info.get("status") == "completed":
            if show_progress:
                print()  # Newline after dots

            conclusion = run_info.get("conclusion")
            if conclusion == "success":
                logger.info("CI passed")
                return ci_status, True
            else:
                logger.info(f"CI completed with conclusion: {conclusion}")
                return ci_status, False

        # CI still running, continue polling
        _show_progress(show_progress)
        time.sleep(poll_interval)

    # Timeout reached
    if show_progress:
        print()
    logger.info("CI polling timeout reached")
    return ci_status, False


def execute_check_branch_status(args: argparse.Namespace) -> int:
    """Execute branch status check command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - ci_timeout: Seconds to wait for CI (0 = no wait)
            - fix: Number of fix attempts (0 = no fix)
            - llm_truncate: Whether to use LLM-friendly output format
            - llm_method: LLM method for fixes (if --fix enabled)
            - mcp_config: Optional MCP configuration path
            - execution_dir: Optional execution directory

    Returns:
        Exit code (0 for success, 1 for failure, 2 for technical error)
    """
    try:
        logger.info("Starting branch status check")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # NEW: Wait for CI completion if timeout specified
        if args.ci_timeout > 0:
            logger.debug(f"CI timeout specified: {args.ci_timeout}s")
            try:
                ci_manager = CIResultsManager(project_dir)
                current_branch = get_current_branch_name(project_dir)

                if not current_branch:
                    logger.error("Could not determine current branch")
                    return 2  # Technical error

                ci_status, ci_success = _wait_for_ci_completion(
                    ci_manager,
                    current_branch,
                    args.ci_timeout,
                    args.llm_truncate,
                )

                # If CI failed after waiting, note for later display
                # (status will be collected again below for full report)
                if not ci_success and ci_status:
                    logger.debug("CI failed after waiting")

            except Exception as e:
                logger.error(f"CI wait failed: {e}")
                return 2  # Technical error

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
        if args.fix > 0:
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

        # NEW: Determine exit code based on CI status
        if report.ci_status == "FAILED":
            return 1  # CI failed

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
