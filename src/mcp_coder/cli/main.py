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
from .commands.create_plan import execute_create_plan
from .commands.create_pr import execute_create_pr
from .commands.define_labels import execute_define_labels
from .commands.gh_tool import execute_get_base_branch
from .commands.git_tool import execute_compact_diff
from .commands.help import execute_help, get_compact_help_text
from .commands.implement import execute_implement
from .commands.init import execute_init
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
    add_git_tool_parsers,
    add_implement_parser,
    add_prompt_parser,
    add_set_status_parser,
    add_verify_parser,
    add_vscodeclaude_parsers,
)

# Logger will be initialized in main()
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Returns:
        Configured ArgumentParser for the mcp-coder CLI.
    """
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
    subparsers.add_parser("init", help="Create default configuration file")
    add_verify_parser(subparsers)

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
    add_git_tool_parsers(subparsers)
    add_vscodeclaude_parsers(subparsers)

    return parser


def handle_no_command(_args: argparse.Namespace) -> int:
    """Handle case when no command is provided.

    Returns:
        Exit code (0 — showing help is valid behavior).
    """
    logger.info("No command provided, showing help")

    help_text = get_compact_help_text()
    print(help_text)

    return 0


def _handle_coordinator_command(args: argparse.Namespace) -> int:
    """Handle coordinator command (flat, no subcommands).

    Returns:
        Exit code from the executed coordinator action.
    """
    if args.dry_run:
        # Validate dry-run args
        if not args.repo:
            print("Error: --dry-run requires --repo NAME", file=sys.stderr)
            return 1
        if not args.branch_name:
            print("Error: --dry-run requires --branch-name BRANCH", file=sys.stderr)
            return 1
        # Map args to what execute_coordinator_test expects
        args.repo_name = args.repo
        args.log_level = args.coordinator_log_level
        return execute_coordinator_test(args)
    else:
        # Validate run args
        if not args.all and not args.repo:
            print("Error: Either --all or --repo must be specified", file=sys.stderr)
            return 1
        return execute_coordinator_run(args)


def _handle_check_command(args: argparse.Namespace) -> int:
    """Handle check subcommands.

    Returns:
        Exit code from the executed check subcommand.
    """
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
    """Handle gh-tool subcommands.

    Returns:
        Exit code from the executed gh-tool subcommand.
    """
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


def _handle_vscodeclaude_command(args: argparse.Namespace) -> int:
    """Handle vscodeclaude subcommands.

    Returns:
        Exit code from the executed vscodeclaude subcommand.
    """
    if hasattr(args, "vscodeclaude_subcommand") and args.vscodeclaude_subcommand:
        if args.vscodeclaude_subcommand == "launch":
            return execute_coordinator_vscodeclaude(args)
        elif args.vscodeclaude_subcommand == "status":
            return execute_coordinator_vscodeclaude_status(args)
        else:
            print(
                f"Error: Unknown vscodeclaude subcommand '{args.vscodeclaude_subcommand}'"
            )
            return 1
    else:
        print("Error: Please specify a subcommand (e.g., 'launch', 'status')")
        return 1


def _handle_git_tool_command(args: argparse.Namespace) -> int:
    """Handle git-tool subcommands.

    Returns:
        Exit code from the executed git-tool subcommand.
    """
    if hasattr(args, "git_tool_subcommand") and args.git_tool_subcommand:
        if args.git_tool_subcommand == "compact-diff":
            return execute_compact_diff(args)
        else:
            logger.error(f"Unknown git-tool subcommand: {args.git_tool_subcommand}")
            print(f"Error: Unknown git-tool subcommand '{args.git_tool_subcommand}'")
            return 1
    else:
        logger.error("git-tool subcommand required")
        print("Error: Please specify a git-tool subcommand (e.g., 'compact-diff')")
        return 1


def _handle_commit_command(args: argparse.Namespace) -> int:
    """Handle commit subcommands.

    Returns:
        Exit code from the executed commit subcommand.
    """
    if args.commit_mode == "auto":
        return execute_commit_auto(args)
    elif args.commit_mode == "clipboard":
        return execute_commit_clipboard(args)
    else:
        logger.error(f"Commit mode '{args.commit_mode}' not yet implemented")
        print(f"Error: Commit mode '{args.commit_mode}' is not yet implemented.")
        return 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for user error, 2 for unexpected error).
    """
    # Ensure stdout/stderr use UTF-8 on all platforms (e.g. Windows cp1252 default).
    # Required by git-tool compact-diff, which outputs raw diff text that may contain
    # Unicode characters (e.g. emoji in commit messages or source files).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

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
        elif args.command == "init":
            return execute_init(args)
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
        elif args.command == "git-tool":
            return _handle_git_tool_command(args)
        elif args.command == "vscodeclaude":
            return _handle_vscodeclaude_command(args)

        # Other commands will be implemented in later steps
        logger.error(f"Command '{args.command}' not yet implemented")
        print(f"Error: Command '{args.command}' is not yet implemented.")
        print("Available commands will be added in upcoming implementation steps.")
        return 1

    except KeyboardInterrupt:
        logger.info("CLI interrupted by user")
        print("\nOperation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in CLI: {e}", exc_info=True)
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
