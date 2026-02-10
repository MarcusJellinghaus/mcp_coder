"""Main CLI entry point for MCP Coder."""

import argparse
import logging
import sys

from .. import __version__
from ..utils.log_utils import setup_logging
from .commands.check_file_sizes import execute_check_file_sizes
from .commands.commit import execute_commit_auto, execute_commit_clipboard
from .commands.coordinator import (
    execute_coordinator_run,
    execute_coordinator_test,
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
)
from .commands.coordinator.issue_stats import execute_coordinator_issue_stats
from .commands.create_plan import execute_create_plan
from .commands.create_pr import execute_create_pr
from .commands.define_labels import execute_define_labels
from .commands.gh_tool import execute_get_base_branch
from .commands.help import execute_help, get_help_text
from .commands.implement import execute_implement
from .commands.prompt import execute_prompt
from .commands.set_status import execute_set_status
from .commands.verify import execute_verify
from .parsers import (
    WideHelpFormatter,
    add_check_parsers,
    add_commit_parsers,
    add_coordinator_parsers,
    add_create_plan_parser,
    add_create_pr_parser,
    add_define_labels_parser,
    add_gh_tool_parsers,
    add_implement_parser,
    add_prompt_parser,
    add_set_status_parser,
)

# Logger will be initialized in main()
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-coder",
        description="AI-powered software development automation toolkit",
        formatter_class=WideHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--log-level",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
        metavar="LEVEL",
    )

    # Add subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND",
    )

    # Simple commands without subparsers
    subparsers.add_parser("help", help="Show help information")
    subparsers.add_parser(
        "verify", help="Verify Claude CLI installation and configuration"
    )

    # Add command parsers from parsers module
    add_prompt_parser(subparsers)
    add_commit_parsers(subparsers)
    add_implement_parser(subparsers)
    add_create_plan_parser(subparsers)
    add_create_pr_parser(subparsers)
    add_coordinator_parsers(subparsers)
    add_define_labels_parser(subparsers)
    add_set_status_parser(subparsers)
    add_check_parsers(subparsers)
    add_gh_tool_parsers(subparsers)

    return parser


def handle_no_command(args: argparse.Namespace) -> int:
    """Handle case when no command is provided."""
    logger.info("No command provided, showing help")

    help_text = get_help_text(include_examples=False)
    print(help_text)

    return 1  # Exit with error code since no command was provided


def _handle_coordinator_command(args: argparse.Namespace) -> int:
    """Handle coordinator subcommands."""
    if hasattr(args, "coordinator_subcommand") and args.coordinator_subcommand:
        if args.coordinator_subcommand == "test":
            return execute_coordinator_test(args)
        elif args.coordinator_subcommand == "run":
            return execute_coordinator_run(args)
        elif args.coordinator_subcommand == "vscodeclaude":
            # Check for status subcommand first
            if (
                hasattr(args, "vscodeclaude_subcommand")
                and args.vscodeclaude_subcommand == "status"
            ):
                return execute_coordinator_vscodeclaude_status(args)
            else:
                return execute_coordinator_vscodeclaude(args)
        elif args.coordinator_subcommand == "issue-stats":
            return execute_coordinator_issue_stats(args)
        else:
            logger.error(
                f"Unknown coordinator subcommand: {args.coordinator_subcommand}"
            )
            print(
                f"Error: Unknown coordinator subcommand '{args.coordinator_subcommand}'"
            )
            return 1
    else:
        logger.error("Coordinator subcommand required")
        print("Error: Please specify a coordinator subcommand (e.g., 'test', 'run')")
        return 1


def _handle_check_command(args: argparse.Namespace) -> int:
    """Handle check subcommands."""
    if hasattr(args, "check_subcommand") and args.check_subcommand:
        if args.check_subcommand == "branch-status":
            from .commands.check_branch_status import execute_check_branch_status

            return execute_check_branch_status(args)
        elif args.check_subcommand == "file-size":
            return execute_check_file_sizes(args)
        else:
            logger.error(f"Unknown check subcommand: {args.check_subcommand}")
            print(f"Error: Unknown check subcommand '{args.check_subcommand}'")
            return 1
    else:
        logger.error("Check subcommand required")
        print(
            "Error: Please specify a check subcommand (e.g., 'branch-status', 'file-size')"
        )
        return 1


def _handle_gh_tool_command(args: argparse.Namespace) -> int:
    """Handle gh-tool subcommands."""
    if hasattr(args, "gh_tool_subcommand") and args.gh_tool_subcommand:
        if args.gh_tool_subcommand == "get-base-branch":
            return execute_get_base_branch(args)
        else:
            logger.error(f"Unknown gh-tool subcommand: {args.gh_tool_subcommand}")
            print(f"Error: Unknown gh-tool subcommand '{args.gh_tool_subcommand}'")
            return 1
    else:
        logger.error("gh-tool subcommand required")
        print("Error: Please specify a gh-tool subcommand (e.g., 'get-base-branch')")
        return 1


def _handle_commit_command(args: argparse.Namespace) -> int:
    """Handle commit subcommands."""
    if args.commit_mode == "auto":
        return execute_commit_auto(args)
    elif args.commit_mode == "clipboard":
        return execute_commit_clipboard(args)
    else:
        logger.error(f"Commit mode '{args.commit_mode}' not yet implemented")
        print(f"Error: Commit mode '{args.commit_mode}' is not yet implemented.")
        return 1


def main() -> int:
    """Main CLI entry point. Returns exit code."""
    # Parse arguments first to get log level
    parser = create_parser()
    args = parser.parse_args()

    # Initialize logging with user-specified level
    setup_logging(args.log_level)

    try:
        logger.debug(
            f"Starting mcp-coder CLI: command={args.command}, log_level={args.log_level}"
        )

        # Handle case when no command is provided
        if not args.command:
            return handle_no_command(args)

        # Route to appropriate command handler
        if args.command == "help":
            return execute_help(args)
        elif args.command == "verify":
            return execute_verify(args)
        elif args.command == "prompt":
            return execute_prompt(args)
        elif args.command == "commit" and hasattr(args, "commit_mode"):
            return _handle_commit_command(args)
        elif args.command == "implement":
            return execute_implement(args)
        elif args.command == "create-plan":
            return execute_create_plan(args)
        elif args.command == "create-pr":
            return execute_create_pr(args)
        elif args.command == "coordinator":
            return _handle_coordinator_command(args)
        elif args.command == "define-labels":
            return execute_define_labels(args)
        elif args.command == "set-status":
            return execute_set_status(args)
        elif args.command == "check":
            return _handle_check_command(args)
        elif args.command == "gh-tool":
            return _handle_gh_tool_command(args)

        # Other commands will be implemented in later steps
        logger.error(f"Command '{args.command}' not yet implemented")
        print(f"Error: Command '{args.command}' is not yet implemented.")
        print("Available commands will be added in upcoming implementation steps.")
        return 1

    except KeyboardInterrupt:
        logger.info("CLI interrupted by user")
        print("\nOperation cancelled by user.")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}", exc_info=True)
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
