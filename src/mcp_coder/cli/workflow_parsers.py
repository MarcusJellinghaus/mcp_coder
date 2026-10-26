"""Argument parser definitions for background-development workflow CLI commands."""

from __future__ import annotations

import argparse
from typing import Any

from .command_catalog import COMMAND_DESCRIPTIONS
from .parsers import WideHelpFormatter
from .shared_args import (
    add_llm_method_arg,
    add_mcp_config_arg,
    add_project_dir_arg,
    add_settings_arg,
)


def add_implement_parser(subparsers: Any) -> None:
    """Add the implement command parser."""
    implement_parser = subparsers.add_parser(
        "implement",
        help=COMMAND_DESCRIPTIONS["implement"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(implement_parser)
    add_llm_method_arg(implement_parser)
    add_mcp_config_arg(implement_parser)
    add_settings_arg(implement_parser)
    implement_parser.add_argument(
        "--update-issue-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Update GitHub issue labels on success/failure (default: from config)",
    )
    implement_parser.add_argument(
        "--post-issue-comments",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post GitHub comments on workflow failure (default: from config)",
    )


def add_review_plan_parser(subparsers: Any) -> None:
    """Add the review-plan command parser."""
    review_plan_parser = subparsers.add_parser(
        "review-plan",
        help=COMMAND_DESCRIPTIONS["review-plan"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(review_plan_parser)
    add_llm_method_arg(review_plan_parser)
    add_mcp_config_arg(review_plan_parser)
    add_settings_arg(review_plan_parser)
    review_plan_parser.add_argument(
        "--update-issue-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Update GitHub issue labels on success/failure (default: from config)",
    )
    review_plan_parser.add_argument(
        "--post-issue-comments",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post GitHub comments on workflow failure (default: from config)",
    )


def add_review_implementation_parser(subparsers: Any) -> None:
    """Add the review-implementation command parser."""
    review_implementation_parser = subparsers.add_parser(
        "review-implementation",
        help=COMMAND_DESCRIPTIONS["review-implementation"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(review_implementation_parser)
    add_llm_method_arg(review_implementation_parser)
    add_mcp_config_arg(review_implementation_parser)
    add_settings_arg(review_implementation_parser)
    review_implementation_parser.add_argument(
        "--update-issue-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Update GitHub issue labels on success/failure (default: from config)",
    )
    review_implementation_parser.add_argument(
        "--post-issue-comments",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post GitHub comments on workflow failure (default: from config)",
    )


def add_create_plan_parser(subparsers: Any) -> None:
    """Add the create-plan command parser."""
    create_plan_parser = subparsers.add_parser(
        "create-plan",
        help=COMMAND_DESCRIPTIONS["create-plan"],
        epilog="Sets failure labels and posts comments on error.",
        formatter_class=WideHelpFormatter,
    )
    create_plan_parser.add_argument(
        "issue_number", type=int, help="GitHub issue number to create plan for"
    )
    add_project_dir_arg(create_plan_parser)
    add_llm_method_arg(create_plan_parser)
    add_mcp_config_arg(create_plan_parser)
    add_settings_arg(create_plan_parser)
    create_plan_parser.add_argument(
        "--update-issue-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Update GitHub issue labels on success/failure (default: from config)",
    )
    create_plan_parser.add_argument(
        "--post-issue-comments",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post GitHub comments on workflow failure (default: from config)",
    )


def add_rebase_parser(subparsers: Any) -> None:
    """Add the rebase command parser."""
    rebase_parser = subparsers.add_parser(
        "rebase",
        help=COMMAND_DESCRIPTIONS["rebase"],
        epilog=(
            "Exit codes: 0 = success or no-op (already current), "
            "1 = aborted / needs human, 2 = error (bad repo/args, push rejected)."
        ),
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(rebase_parser)
    add_llm_method_arg(rebase_parser)
    add_mcp_config_arg(rebase_parser)
    add_settings_arg(rebase_parser)
    rebase_parser.add_argument(
        "--base-branch",
        type=str,
        default=None,
        metavar="BRANCH",
        help="Base branch to rebase onto (default: auto-detect; needed only when "
        "the detected base is not main/master and not named in the issue's "
        "### Base Branch; only honoured when the issue body is trusted — see "
        "docs/repository-setup/github.md)",
    )


def add_create_pr_parser(subparsers: Any) -> None:
    """Add the create-pr command parser."""
    create_pr_parser = subparsers.add_parser(
        "create-pr",
        help=COMMAND_DESCRIPTIONS["create-pr"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(create_pr_parser)
    add_llm_method_arg(create_pr_parser)
    add_mcp_config_arg(create_pr_parser)
    add_settings_arg(create_pr_parser)
    create_pr_parser.add_argument(
        "--update-issue-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Update GitHub issue labels on success/failure (default: from config)",
    )
    create_pr_parser.add_argument(
        "--post-issue-comments",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post GitHub comments on workflow failure (default: from config)",
    )


def add_fix_conflict_parser(subparsers: Any) -> None:
    """Add the fix-conflict command parser (project-dir only, no LLM args)."""
    fix_conflict_parser = subparsers.add_parser(
        "fix-conflict",
        help=COMMAND_DESCRIPTIONS["fix-conflict"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(fix_conflict_parser)


def add_fix_ci_parser(subparsers: Any) -> None:
    """Add the fix-ci command parser."""
    fix_ci_parser = subparsers.add_parser(
        "fix-ci",
        help=COMMAND_DESCRIPTIONS["fix-ci"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(fix_ci_parser)
    add_llm_method_arg(fix_ci_parser)
    add_mcp_config_arg(fix_ci_parser)
    add_settings_arg(fix_ci_parser)
    fix_ci_parser.add_argument(
        "--update-issue-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Update GitHub issue labels on success/failure (default: from config)",
    )
    fix_ci_parser.add_argument(
        "--post-issue-comments",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post GitHub comments on workflow failure (default: from config)",
    )


def add_coordinator_parsers(subparsers: Any) -> None:
    """Add coordinator command parser (direct command, no subcommands)."""
    coordinator_parser = subparsers.add_parser(
        "coordinator",
        help=COMMAND_DESCRIPTIONS["coordinator"],
        formatter_class=WideHelpFormatter,
    )

    # --dry-run mode (replaces old "coordinator test")
    coordinator_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Trigger Jenkins test instead of dispatching workflows",
    )

    # Run mode args (--all or --repo, mutually exclusive)
    run_group = coordinator_parser.add_mutually_exclusive_group()
    run_group.add_argument(
        "--all", action="store_true", help="Process all repositories from config"
    )
    run_group.add_argument(
        "--repo",
        type=str,
        metavar="NAME",
        help="Process single repository (e.g., mcp_coder)",
    )

    coordinator_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force full cache refresh, bypass all caching",
    )

    # Dry-run specific args (for Jenkins test trigger)
    coordinator_parser.add_argument(
        "--branch-name",
        type=str,
        help="Git branch to test (required with --dry-run)",
    )
    coordinator_parser.add_argument(
        "--log-level-coordinator",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
        help="Log level for mcp-coder commands in test script (default: DEBUG)",
        metavar="LEVEL",
        dest="coordinator_log_level",
    )
