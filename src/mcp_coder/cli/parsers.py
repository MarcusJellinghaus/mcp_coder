"""Argument parser definitions for MCP Coder CLI commands.

This module contains functions that add subparser configurations for
each CLI command. Separating these from main.py helps manage file size
and improves maintainability.
"""

from __future__ import annotations

import argparse
from typing import Any

from .commands.set_status import build_set_status_epilog


class WideHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter with wider help position for longer command names."""

    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 32,
        width: int | None = None,
    ) -> None:
        super().__init__(prog, indent_increment, max_help_position, width)


def add_prompt_parser(subparsers: Any) -> None:
    """Add the prompt command parser."""
    prompt_parser = subparsers.add_parser(
        "prompt",
        help="Execute prompt via Claude API with configurable debug output",
        formatter_class=WideHelpFormatter,
    )
    prompt_parser.add_argument("prompt", help="The prompt to send to Claude")
    prompt_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    prompt_parser.add_argument(
        "--verbosity",
        choices=["just-text", "verbose", "raw"],
        default="just-text",
        help="Output detail: just-text (response only), verbose (+ metrics), raw (+ full JSON)",
    )
    prompt_parser.add_argument(
        "--store-response",
        action="store_true",
        help="Save session to .mcp-coder/responses/ for later continuation",
    )

    # Session continuation options (mutually exclusive with each other)
    continue_group = prompt_parser.add_mutually_exclusive_group()
    continue_group.add_argument(
        "--continue-session-from",
        type=str,
        metavar="FILE",
        help="Resume conversation from specific stored session file",
    )
    continue_group.add_argument(
        "--continue-session",
        action="store_true",
        help="Resume from most recent session (auto-discovers latest file)",
    )

    prompt_parser.add_argument(
        "--session-id",
        type=str,
        metavar="ID",
        help="Direct session ID for continuation (overrides file-based options)",
    )
    prompt_parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECONDS",
        help="API request timeout in seconds (default: 60)",
    )
    prompt_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        metavar="METHOD",
        help="Communication method: claude_code_cli (default) or claude_code_api",
    )
    prompt_parser.add_argument(
        "--output-format",
        choices=["text", "json", "session-id"],
        default="text",
        metavar="FORMAT",
        help="Output format: text (default), json (includes session_id), or session-id (only session_id)",
    )
    prompt_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file (e.g., .mcp.linux.json)",
    )
    prompt_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Working directory for Claude subprocess (default: current directory)",
    )


def add_commit_parsers(subparsers: Any) -> None:
    """Add commit command parsers (auto, clipboard)."""
    commit_parser = subparsers.add_parser("commit", help="Git commit operations")
    commit_subparsers = commit_parser.add_subparsers(
        dest="commit_mode", help="Available commit modes", metavar="MODE"
    )

    # commit auto command
    auto_parser = commit_subparsers.add_parser(
        "auto",
        help="Auto-generate commit message using LLM",
        formatter_class=WideHelpFormatter,
    )
    auto_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show generated message and ask for confirmation before committing",
    )
    auto_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    auto_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    auto_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file (e.g., .mcp.linux.json)",
    )
    auto_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Working directory for Claude subprocess (default: current directory)",
    )

    # commit clipboard command
    clipboard_parser = commit_subparsers.add_parser(
        "clipboard",
        help="Use commit message from clipboard",
        formatter_class=WideHelpFormatter,
    )
    clipboard_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )


def add_implement_parser(subparsers: Any) -> None:
    """Add the implement command parser."""
    implement_parser = subparsers.add_parser(
        "implement",
        help="Execute implementation workflow from task tracker",
        formatter_class=WideHelpFormatter,
    )
    implement_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    implement_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    implement_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file (e.g., .mcp.linux.json)",
    )
    implement_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Working directory for Claude subprocess (default: current directory)",
    )
    implement_parser.add_argument(
        "--update-labels",
        action="store_true",
        help="Automatically update GitHub issue labels on successful completion",
    )


def add_create_plan_parser(subparsers: Any) -> None:
    """Add the create-plan command parser."""
    create_plan_parser = subparsers.add_parser(
        "create-plan",
        help="Generate implementation plan for a GitHub issue",
        formatter_class=WideHelpFormatter,
    )
    create_plan_parser.add_argument(
        "issue_number", type=int, help="GitHub issue number to create plan for"
    )
    create_plan_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    create_plan_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    create_plan_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file (e.g., .mcp.linux.json)",
    )
    create_plan_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Working directory for Claude subprocess (default: current directory)",
    )
    create_plan_parser.add_argument(
        "--update-labels",
        action="store_true",
        help="Automatically update GitHub issue labels on successful completion",
    )


def add_create_pr_parser(subparsers: Any) -> None:
    """Add the create-pr command parser."""
    create_pr_parser = subparsers.add_parser(
        "create-pr",
        help="Create pull request with AI-generated summary",
        formatter_class=WideHelpFormatter,
    )
    create_pr_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    create_pr_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    create_pr_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file (e.g., .mcp.linux.json)",
    )
    create_pr_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Working directory for Claude subprocess (default: current directory)",
    )
    create_pr_parser.add_argument(
        "--update-labels",
        action="store_true",
        help="Automatically update GitHub issue labels on successful completion",
    )


def add_coordinator_parsers(subparsers: Any) -> None:
    """Add coordinator command parsers."""
    coordinator_parser = subparsers.add_parser(
        "coordinator", help="Coordinator commands for repository testing"
    )
    coordinator_subparsers = coordinator_parser.add_subparsers(
        dest="coordinator_subcommand",
        help="Available coordinator commands",
        metavar="SUBCOMMAND",
    )

    # coordinator test command
    test_parser = coordinator_subparsers.add_parser(
        "test",
        help="Trigger Jenkins integration test for repository",
        formatter_class=WideHelpFormatter,
    )
    test_parser.add_argument(
        "repo_name", help="Repository name from config (e.g., mcp_coder)"
    )
    test_parser.add_argument(
        "--branch-name",
        required=True,
        help="Git branch to test (e.g., feature-x, main)",
    )
    test_parser.add_argument(
        "--log-level",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
        help="Log level for mcp-coder commands in test script (default: DEBUG)",
        metavar="LEVEL",
    )

    # coordinator run command
    run_parser = coordinator_subparsers.add_parser(
        "run",
        help="Monitor and dispatch workflows for GitHub issues",
        formatter_class=WideHelpFormatter,
    )

    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument(
        "--all", action="store_true", help="Process all repositories from config"
    )
    run_group.add_argument(
        "--repo",
        type=str,
        metavar="NAME",
        help="Process single repository (e.g., mcp_coder)",
    )

    run_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force full cache refresh, bypass all caching",
    )

    # coordinator vscodeclaude command
    vscodeclaude_parser = coordinator_subparsers.add_parser(
        "vscodeclaude",
        help="Manage VSCode/Claude sessions for interactive workflow stages",
        epilog="Documentation: https://github.com/MarcusJellinghaus/mcp_coder/blob/main/docs/coordinator-vscodeclaude.md",
    )
    vscodeclaude_subparsers = vscodeclaude_parser.add_subparsers(
        dest="vscodeclaude_subcommand",
        help="VSCodeClaude commands",
        metavar="SUBCOMMAND",
    )

    vscodeclaude_parser.add_argument(
        "--repo",
        type=str,
        metavar="NAME",
        help="Filter to specific repository only",
    )
    vscodeclaude_parser.add_argument(
        "--max-sessions",
        type=int,
        metavar="N",
        help="Override max concurrent sessions (default: from config or 3)",
    )
    vscodeclaude_parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete stale clean folders (without this flag, only lists them)",
    )
    vscodeclaude_parser.add_argument(
        "--intervene",
        action="store_true",
        help="Force open a bot_busy issue for debugging",
    )
    vscodeclaude_parser.add_argument(
        "--issue",
        type=int,
        metavar="NUMBER",
        help="Issue number for intervention mode (requires --intervene)",
    )

    # vscodeclaude status subcommand
    status_parser = vscodeclaude_subparsers.add_parser(
        "status",
        help="Show current VSCodeClaude sessions",
    )
    status_parser.add_argument(
        "--repo",
        type=str,
        metavar="NAME",
        help="Filter to specific repository only",
    )

    # coordinator issue-stats command
    issue_stats_parser = coordinator_subparsers.add_parser(
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
        help="Project directory path (default: current directory)",
    )


def add_define_labels_parser(subparsers: Any) -> None:
    """Add the define-labels command parser."""
    define_labels_parser = subparsers.add_parser(
        "define-labels",
        help="Sync workflow status labels to GitHub repository",
        formatter_class=WideHelpFormatter,
    )
    define_labels_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    define_labels_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )


def add_set_status_parser(subparsers: Any) -> None:
    """Add the set-status command parser."""
    set_status_parser = subparsers.add_parser(
        "set-status",
        help="Update GitHub issue workflow status label",
        formatter_class=WideHelpFormatter,
        epilog=build_set_status_epilog(),
    )
    set_status_parser.add_argument(
        "status_label",
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
        help="Project directory path (default: current directory)",
    )
    set_status_parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass clean working directory check",
    )


def add_check_parsers(subparsers: Any) -> None:
    """Add check command parsers (branch-status, file-size)."""
    check_parser = subparsers.add_parser(
        "check", help="Check commands for branch and code status verification"
    )
    check_subparsers = check_parser.add_subparsers(
        dest="check_subcommand",
        help="Available check commands",
        metavar="SUBCOMMAND",
    )

    # check branch-status command
    branch_status_parser = check_subparsers.add_parser(
        "branch-status",
        help="Check branch readiness status and optionally apply fixes",
        formatter_class=WideHelpFormatter,
    )
    branch_status_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    branch_status_parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix issues found",
    )
    branch_status_parser.add_argument(
        "--llm-truncate",
        action="store_true",
        help="Truncate output for LLM consumption",
    )
    branch_status_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use for --fix (default: claude_code_cli)",
    )
    branch_status_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file (e.g., .mcp.linux.json)",
    )
    branch_status_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Working directory for Claude subprocess (default: current directory)",
    )

    # check file-size command
    file_size_parser = check_subparsers.add_parser(
        "file-size",
        help="Check file sizes against maximum line count",
        formatter_class=WideHelpFormatter,
    )
    file_size_parser.add_argument(
        "--max-lines",
        type=int,
        default=600,
        help="Maximum lines per file (default: 600)",
    )
    file_size_parser.add_argument(
        "--allowlist-file",
        type=str,
        default=".large-files-allowlist",
        help="Path to allowlist file (default: .large-files-allowlist)",
    )
    file_size_parser.add_argument(
        "--generate-allowlist",
        action="store_true",
        help="Output violating paths for piping to allowlist",
    )
    file_size_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )


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
        help="Project directory path (default: current directory)",
    )
