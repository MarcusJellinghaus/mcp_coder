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
        help="Sync workflow label definitions to a GitHub repository",
        description="Sync workflow label definitions to a GitHub repository.",
        epilog="""Operations (always):
  - Validate labels config (default label, promotable targets)
  - Create, update, and delete status-* label definitions from config

With --init:
  - Assign the default label to open issues without a status label

With --validate:
  - Check all open issues for errors (multiple status labels)
    and warnings (stale bot processes)

With --generate-github-actions:
  - Write label-new-issues.yml and approve-command.yml
    to {project_dir}/.github/workflows/

With --all:
  - Run all optional operations (--init --validate --generate-github-actions)

Config resolution:
  1. --config PATH (explicit, highest priority)
  2. [tool.mcp-coder] labels-config in pyproject.toml
  3. Bundled package defaults""",
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
    define_labels_parser.add_argument(
        "--init",
        action="store_true",
        help="Assign the default label to open issues without a status label",
    )
    define_labels_parser.add_argument(
        "--validate",
        action="store_true",
        help="Check all open issues for errors and warnings",
    )
    define_labels_parser.add_argument(
        "--config",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to labels config file (overrides pyproject.toml and bundled defaults)",
    )
    define_labels_parser.add_argument(
        "--generate-github-actions",
        action="store_true",
        help="Write label-new-issues.yml and approve-command.yml to .github/workflows/",
    )
    define_labels_parser.add_argument(
        "--all",
        action="store_true",
        help="Enable all optional operations (--init --validate --generate-github-actions)",
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
    set_status_parser.add_argument(
        "--from-status",
        type=str,
        default=None,
        help="Only update if current status matches this label (precondition guard)",
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
