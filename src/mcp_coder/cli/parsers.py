"""Argument parser definitions for MCP Coder CLI commands.

This module contains functions that add subparser configurations for
each CLI command. Separating these from main.py helps manage file size
and improves maintainability.
"""

from __future__ import annotations

import argparse
from typing import Any


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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
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
        choices=["claude", "langchain"],
        default=None,
        metavar="METHOD",
        help="LLM method override. If omitted, uses config default_provider or claude",
    )
    prompt_parser.add_argument(
        "--output-format",
        choices=["text", "json", "session-id", "ndjson", "json-raw"],
        default="text",
        metavar="FORMAT",
        help="Output format: text (default), json (complete response), session-id (only session_id), ndjson (streaming NDJSON events), json-raw (raw NDJSON lines from CLI)",
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
        help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory",
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
        choices=["claude", "langchain"],
        default=None,
        help="LLM method override. If omitted, uses config default_provider or claude",
    )
    auto_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    auto_parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory",
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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    implement_parser.add_argument(
        "--llm-method",
        choices=["claude", "langchain"],
        default=None,
        help="LLM method override. If omitted, uses config default_provider or claude",
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
        help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory",
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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    create_plan_parser.add_argument(
        "--llm-method",
        choices=["claude", "langchain"],
        default=None,
        help="LLM method override. If omitted, uses config default_provider or claude",
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
        help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory",
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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    create_pr_parser.add_argument(
        "--llm-method",
        choices=["claude", "langchain"],
        default=None,
        help="LLM method override. If omitted, uses config default_provider or claude",
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
        help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory",
    )
    create_pr_parser.add_argument(
        "--update-labels",
        action="store_true",
        help="Automatically update GitHub issue labels on successful completion",
    )


def add_coordinator_parsers(subparsers: Any) -> None:
    """Add coordinator command parser (direct command, no subcommands)."""
    coordinator_parser = subparsers.add_parser(
        "coordinator",
        help="Monitor and dispatch workflows for GitHub issues",
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


def _validate_ci_timeout(value: str) -> int:
    """Validate ci-timeout argument is non-negative integer.

    Returns:
        Validated non-negative integer value.

    Raises:
        ArgumentTypeError: If value is not a non-negative integer.
    """
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("--ci-timeout must be non-negative")
        return ivalue
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--ci-timeout must be an integer") from exc


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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    branch_status_parser.add_argument(
        "--ci-timeout",
        type=_validate_ci_timeout,
        default=0,
        metavar="SECONDS",
        help="Wait up to N seconds for CI completion (default: 0 = no wait)",
    )
    branch_status_parser.add_argument(
        "--fix",
        nargs="?",
        type=int,
        const=1,
        default=0,
        metavar="N",
        help="Fix issues up to N times (default: 0 = no fix, --fix alone = 1)",
    )
    branch_status_parser.add_argument(
        "--llm-truncate",
        action="store_true",
        help="Truncate output for LLM consumption",
    )
    branch_status_parser.add_argument(
        "--llm-method",
        choices=["claude", "langchain"],
        default=None,
        help="LLM method override. If omitted, uses config default_provider or claude",
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
        help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory",
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
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
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


def add_verify_parser(subparsers: Any) -> None:
    """Add the verify command parser."""
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify CLI installation, LLM provider, and MLflow configuration",
        formatter_class=WideHelpFormatter,
    )
    verify_parser.add_argument(
        "--check-models",
        action="store_true",
        help="List available models for the configured LangChain backend (requires network)",
    )
    verify_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory: where source code lives (git operations, file modifications). Default: current directory",
    )
    verify_parser.add_argument(
        "--llm-method",
        choices=["claude", "langchain"],
        default=None,
        metavar="METHOD",
        help="LLM method override. If omitted, uses config default_provider or claude",
    )
    verify_parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to .mcp.json for MCP agent smoke test",
    )


def add_vscodeclaude_parsers(subparsers: Any) -> None:
    """Add vscodeclaude command parsers."""
    vscodeclaude_parser = subparsers.add_parser(
        "vscodeclaude",
        help="Manage VSCode/Claude sessions for interactive workflow stages",
    )
    vscodeclaude_subparsers = vscodeclaude_parser.add_subparsers(
        dest="vscodeclaude_subcommand",
        help="VSCodeClaude commands",
        metavar="SUBCOMMAND",
    )

    # vscodeclaude launch
    launch_parser = vscodeclaude_subparsers.add_parser(
        "launch",
        help="Launch VSCode/Claude sessions for issues needing review",
        formatter_class=WideHelpFormatter,
    )
    launch_parser.add_argument(
        "--repo",
        type=str,
        metavar="NAME",
        help="Filter to specific repository only",
    )
    launch_parser.add_argument(
        "--max-sessions",
        type=int,
        metavar="N",
        help="Override max concurrent sessions (default: from config or 3)",
    )
    launch_parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete stale clean folders (without this flag, only lists them)",
    )
    launch_parser.add_argument(
        "--intervene",
        action="store_true",
        help="Force open a bot_busy issue for debugging",
    )
    launch_parser.add_argument(
        "--issue",
        type=int,
        metavar="NUMBER",
        help="Issue number for intervention mode (requires --intervene)",
    )

    # vscodeclaude status
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
