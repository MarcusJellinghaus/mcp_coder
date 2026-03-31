"""Argument parser definitions for GitHub and Git tool CLI commands.

Extracted from parsers.py to keep file sizes within project limits.
"""

from __future__ import annotations

from typing import Any

from .parsers import WideHelpFormatter


def add_gh_tool_parsers(subparsers: Any) -> None:
    """Add gh-tool command parsers."""
    gh_tool_parser = subparsers.add_parser("gh-tool", help="GitHub tool commands")
    gh_tool_subparsers = gh_tool_parser.add_subparsers(
        dest="gh_tool_subcommand",
        help="Available GitHub tool commands",
        metavar="SUBCOMMAND",
    )

    # gh-tool get-base-branch command
    get_base_branch_parser = gh_tool_subparsers.add_parser(
        "get-base-branch",
        help="Detect base branch for current feature branch",
        formatter_class=WideHelpFormatter,
        epilog="""Exit codes:
  0  Success - base branch printed to stdout
  1  Could not detect base branch
  2  Error (not a git repo, API failure)""",
    )
    get_base_branch_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )

    # gh-tool define-labels (moved from top-level)
    define_labels_parser = gh_tool_subparsers.add_parser(
        "define-labels",
        help="Sync workflow status labels to GitHub repository",
        formatter_class=WideHelpFormatter,
    )
    define_labels_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory. Default: current directory",
    )
    define_labels_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )

    # gh-tool issue-stats (moved from coordinator)
    issue_stats_parser = gh_tool_subparsers.add_parser(
        "issue-stats",
        help="Display issue statistics by workflow status",
        formatter_class=WideHelpFormatter,
    )
    issue_stats_parser.add_argument(
        "--filter",
        type=str.lower,
        choices=["all", "human", "bot"],
        default="all",
        help="Filter issues by category (default: all)",
    )
    issue_stats_parser.add_argument(
        "--details",
        action="store_true",
        default=False,
        help="Show individual issue details with links",
    )
    issue_stats_parser.add_argument(
        "--project-dir",
        metavar="PATH",
        help="Project directory. Default: current directory",
    )

    # gh-tool checkout-issue-branch command
    checkout_branch_parser = gh_tool_subparsers.add_parser(
        "checkout-issue-branch",
        help="Checkout or create a branch linked to a GitHub issue",
        formatter_class=WideHelpFormatter,
        epilog="""Exit codes:
  0  Success - branch checked out
  1  Could not find or create branch
  2  Error (not a git repo, API failure)""",
    )
    checkout_branch_parser.add_argument(
        "issue_number", type=int, help="GitHub issue number"
    )
    checkout_branch_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory: where source code lives. Default: current directory",
    )

    # gh-tool set-status command
    from .commands.set_status import build_set_status_epilog

    set_status_parser = gh_tool_subparsers.add_parser(
        "set-status",
        help="Update GitHub issue workflow status label",
        formatter_class=WideHelpFormatter,
        epilog=build_set_status_epilog(),
    )
    set_status_parser.add_argument(
        "status_label",
        nargs="?",
        default=None,
        help="Status label to set (e.g., status-05:plan-ready)",
    )
    set_status_parser.add_argument(
        "--issue",
        type=int,
        default=None,
        help="Issue number (default: auto-detect from branch name)",
    )
    set_status_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    set_status_parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass clean working directory check",
    )


def add_git_tool_parsers(subparsers: Any) -> None:
    """Add git-tool command parsers."""
    git_tool_parser = subparsers.add_parser("git-tool", help="Git tool commands")
    git_tool_subparsers = git_tool_parser.add_subparsers(
        dest="git_tool_subcommand",
        help="Available Git tool commands",
        metavar="SUBCOMMAND",
    )

    # git-tool compact-diff command
    compact_diff_parser = git_tool_subparsers.add_parser(
        "compact-diff",
        help="Generate compact diff suppressing moved-code blocks",
        formatter_class=WideHelpFormatter,
        epilog="""Exit codes:
  0  Success - compact diff printed to stdout
  1  Could not detect base branch
  2  Error (invalid repo, unexpected exception)""",
    )
    compact_diff_parser.add_argument(
        "--base-branch",
        type=str,
        default=None,
        help="Base branch to diff against (default: auto-detected)",
    )
    compact_diff_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    compact_diff_parser.add_argument(
        "--exclude",
        action="append",
        metavar="PATTERN",
        help="Exclude files matching pattern (repeatable)",
    )
    compact_diff_parser.add_argument(
        "--committed-only",
        action="store_true",
        help="Show only committed changes (exclude uncommitted changes from output)",
    )
