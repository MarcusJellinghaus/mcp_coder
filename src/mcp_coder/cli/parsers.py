"""Argument parser definitions for MCP Coder CLI commands.

This module contains functions that add subparser configurations for
each CLI command. Separating these from main.py helps manage file size
and improves maintainability.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, NoReturn

from .command_catalog import COMMAND_DESCRIPTIONS
from .shared_args import (
    add_execution_dir_arg,
    add_llm_method_arg,
    add_mcp_config_arg,
    add_project_dir_arg,
    add_settings_arg,
)


class HelpHintArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass that appends a help hint on errors.

    On parse errors, prints a GNU-style hint:
        Try '<prog> --help' for more information.

    Subparsers automatically inherit this class via argparse internals.
    """

    def error(self, message: str) -> NoReturn:
        """Print usage, error message, and help hint, then exit with code 2."""
        self.print_usage(sys.stderr)
        self._print_message(f"{self.prog}: error: {message}\n", sys.stderr)
        self._print_message(
            f"Try '{self.prog} --help' for more information.\n", sys.stderr
        )
        self.exit(2)


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
        help=COMMAND_DESCRIPTIONS["prompt"],
        formatter_class=WideHelpFormatter,
    )
    prompt_parser.add_argument("prompt", help="The prompt to send to Claude")
    add_project_dir_arg(prompt_parser)
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
    add_llm_method_arg(prompt_parser)
    prompt_parser.add_argument(
        "--output-format",
        choices=["rendered", "text", "json", "session-id", "ndjson", "json-raw"],
        default="rendered",
        metavar="FORMAT",
        help="Output format: rendered (default, human-friendly streaming), text (plain streaming), ndjson (streaming NDJSON events), json-raw (streaming raw events), json (blocking, complete response), session-id (blocking, only session_id)",
    )
    add_mcp_config_arg(prompt_parser)
    add_settings_arg(prompt_parser)
    prompt_parser.add_argument(
        "--add-system-prompts",
        action="store_true",
        help="Inject system and project prompts into the LLM request",
    )
    add_execution_dir_arg(prompt_parser)


def add_commit_parsers(subparsers: Any) -> None:
    """Add commit command parsers (auto)."""
    commit_parser = subparsers.add_parser("commit", help="Git commit operations")
    commit_subparsers = commit_parser.add_subparsers(
        dest="commit_mode", help="Available commit modes", metavar="MODE"
    )

    # commit auto command
    auto_parser = commit_subparsers.add_parser(
        "auto",
        help=COMMAND_DESCRIPTIONS["commit auto"],
        formatter_class=WideHelpFormatter,
    )
    auto_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show generated message and ask for confirmation before committing",
    )
    add_llm_method_arg(auto_parser)
    add_project_dir_arg(auto_parser)
    add_execution_dir_arg(auto_parser)
    auto_parser.add_argument(
        "--push",
        action="store_true",
        help="Push to origin after successful commit",
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
    add_execution_dir_arg(implement_parser)
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
    add_execution_dir_arg(create_plan_parser)
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
    add_execution_dir_arg(create_pr_parser)
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


def _validate_pr_timeout(value: str) -> int:
    """Validate pr-timeout argument is non-negative integer.

    Returns:
        Validated non-negative integer value.

    Raises:
        ArgumentTypeError: If value is not a non-negative integer.
    """
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("--pr-timeout must be non-negative")
        return ivalue
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--pr-timeout must be an integer") from exc


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
        help=COMMAND_DESCRIPTIONS["check branch-status"],
        formatter_class=WideHelpFormatter,
    )
    add_project_dir_arg(branch_status_parser)
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
    add_llm_method_arg(branch_status_parser)
    add_mcp_config_arg(branch_status_parser)
    add_settings_arg(branch_status_parser)
    add_execution_dir_arg(branch_status_parser)
    branch_status_parser.add_argument(
        "--wait-for-pr",
        action="store_true",
        help="Wait for PR creation, then proceed with normal branch-status check",
    )
    branch_status_parser.add_argument(
        "--pr-timeout",
        type=_validate_pr_timeout,
        default=600,
        metavar="SECONDS",
        help="Max seconds to wait for PR to appear (default: 600) (only used with --wait-for-pr)",
    )

    # check file-size command
    file_size_parser = check_subparsers.add_parser(
        "file-size",
        help=COMMAND_DESCRIPTIONS["check file-size"],
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
    add_project_dir_arg(file_size_parser)


def add_verify_parser(subparsers: Any) -> None:
    """Add the verify command parser."""
    verify_parser = subparsers.add_parser(
        "verify",
        help=COMMAND_DESCRIPTIONS["verify"],
        formatter_class=WideHelpFormatter,
    )
    verify_parser.add_argument(
        "--check-models",
        action="store_true",
        help="List available models for the configured LangChain backend (requires network)",
    )
    add_project_dir_arg(verify_parser)
    add_llm_method_arg(verify_parser)
    add_mcp_config_arg(verify_parser, help="Path to .mcp.json for MCP agent smoke test")
    add_settings_arg(verify_parser)
    verify_parser.add_argument(
        "--list-mcp-tools",
        action="store_true",
        help="List MCP tools with descriptions grouped by server",
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
        help=COMMAND_DESCRIPTIONS["vscodeclaude launch"],
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
    launch_parser.add_argument(
        "--no-install-from-github",
        action="store_true",
        help="Skip installing packages from GitHub even when configured in pyproject.toml",
    )

    # vscodeclaude status
    status_parser = vscodeclaude_subparsers.add_parser(
        "status",
        help=COMMAND_DESCRIPTIONS["vscodeclaude status"],
    )
    status_parser.add_argument(
        "--repo",
        type=str,
        metavar="NAME",
        help="Filter to specific repository only",
    )
    status_parser.add_argument(
        "--explain",
        action="store_true",
        help="Dump the full detection signals and decision per session (read-only)",
    )


def add_init_parser(subparsers: Any) -> None:
    """Add the init command parser."""
    init_parser = subparsers.add_parser(
        "init",
        help=COMMAND_DESCRIPTIONS["init"],
        formatter_class=WideHelpFormatter,
    )
    init_parser.add_argument(
        "--just-skills",
        action="store_true",
        help="Deploy skills only, skip config creation",
    )
    add_project_dir_arg(
        init_parser, help="Target project directory (default: current directory)"
    )


def add_icoder_parser(subparsers: Any) -> None:
    """Add the icoder command parser."""
    icoder_parser = subparsers.add_parser(
        "icoder",
        help=COMMAND_DESCRIPTIONS["icoder"],
        formatter_class=WideHelpFormatter,
    )
    add_llm_method_arg(icoder_parser)
    add_mcp_config_arg(icoder_parser)
    add_settings_arg(icoder_parser)
    add_project_dir_arg(icoder_parser)
    add_execution_dir_arg(icoder_parser)
    icoder_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        metavar="SECONDS",
        help="LLM inactivity timeout in seconds — max silence before cancelling (default: 300)",
    )
    icoder_parser.add_argument(
        "--no-format-tools",
        action="store_true",
        help="Disable tool output formatting (show raw output)",
    )

    # Session continuation options (all three are mutually exclusive)
    continue_group = icoder_parser.add_mutually_exclusive_group()
    continue_group.add_argument(
        "--continue-session-from",
        type=str,
        metavar="FILE",
        help="Resume conversation from a specific .jsonl event-log file",
    )
    continue_group.add_argument(
        "--continue-session",
        action="store_true",
        help="Open a session picker over prior icoder logs in the project",
    )
    continue_group.add_argument(
        "--session-id",
        type=str,
        metavar="ID",
        help="Direct session ID for continuation",
    )
    icoder_parser.add_argument(
        "--initial-color",
        type=str,
        default=None,
        metavar="COLOR",
        help="Set prompt border color at startup (named color or hex code)",
    )
    icoder_parser.add_argument(
        "--tool-display",
        choices=["oneline", "compressed"],
        default="compressed",
        help="Default tier for tool display blocks (default: compressed)",
    )
