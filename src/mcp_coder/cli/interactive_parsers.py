"""Argument parser definitions for interactive-development CLI commands."""

from __future__ import annotations

from typing import Any

from .command_catalog import COMMAND_DESCRIPTIONS
from .parsers import WideHelpFormatter
from .shared_args import (
    add_llm_method_arg,
    add_mcp_config_arg,
    add_project_dir_arg,
    add_settings_arg,
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
