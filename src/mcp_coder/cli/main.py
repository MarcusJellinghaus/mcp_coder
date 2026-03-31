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
from .commands.gh_tool import execute_checkout_issue_branch, execute_get_base_branch
from .commands.git_tool import execute_compact_diff
from .commands.help import get_help_text
from .commands.icoder import execute_icoder
from .commands.implement import execute_implement
from .commands.init import execute_init
from .commands.prompt import execute_prompt
from .commands.verify import execute_verify
from .gh_parsers import add_gh_tool_parsers, add_git_tool_parsers
from .parsers import (
    HelpHintArgumentParser,
    WideHelpFormatter,
    add_check_parsers,
    add_commit_parsers,
    add_coordinator_parsers,
    add_create_plan_parser,
    add_create_pr_parser,
    add_icoder_parser,
    add_implement_parser,
    add_prompt_parser,
    add_verify_parser,
    add_vscodeclaude_parsers,
)

# Logger will be initialized in main()
logger = logging.getLogger(__name__)

_INFO_COMMANDS = frozenset({"create-plan", "implement", "create-pr", "coordinator"})


def _resolve_log_level(args: argparse.Namespace) -> str:
    """Resolve the effective log level based on command and explicit flag.

    Workflow commands default to INFO; other commands default to NOTICE.
    An explicit --log-level always wins.

    Returns:
        The log level string to pass to setup_logging.
    """
    if args.log_level is not None:
        return str(args.log_level)
    if args.command in _INFO_COMMANDS:
        return "INFO"
    if (
        args.command == "vscodeclaude"
        and getattr(args, "vscodeclaude_subcommand", None) == "launch"
    ):
        return "INFO"
    return "NOTICE"


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Returns:
        Configured ArgumentParser for the mcp-coder CLI.
    """
    parser = HelpHintArgumentParser(
        prog="mcp-coder",
        description="AI-powered software development automation toolkit",
        formatter_class=WideHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "--help",
        "-h",
        action="store_true",
        default=False,
        dest="help",
        help=argparse.SUPPRESS,
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
        default=None,
        help="Set the logging level (default: NOTICE, or INFO for workflow commands)",
        metavar="LEVEL",
    )

    # Add subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND",
    )

    # Simple commands without subparsers
    subparsers.add_parser("help", help=argparse.SUPPRESS)
    subparsers.add_parser("init", help="Create default configuration file")
    add_verify_parser(subparsers)

    # Add command parsers from parsers module
    add_prompt_parser(subparsers)
    add_commit_parsers(subparsers)
    add_implement_parser(subparsers)
    add_icoder_parser(subparsers)
    add_create_plan_parser(subparsers)
    add_create_pr_parser(subparsers)
    add_coordinator_parsers(subparsers)
    add_check_parsers(subparsers)
    add_gh_tool_parsers(subparsers)
    add_git_tool_parsers(subparsers)
    add_vscodeclaude_parsers(subparsers)

    return parser


def _handle_coordinator_command(args: argparse.Namespace) -> int:
    """Handle coordinator command (flat, no subcommands).

    Returns:
        Exit code from the executed coordinator action.
    """
    if args.dry_run:
        # Validate dry-run args
        if not args.repo:
            print("Error: --dry-run requires --repo NAME", file=sys.stderr)
            print(
                "Try 'mcp-coder coordinator --help' for more information.",
                file=sys.stderr,
            )
            return 1
        if not args.branch_name:
            print("Error: --dry-run requires --branch-name BRANCH", file=sys.stderr)
            print(
                "Try 'mcp-coder coordinator --help' for more information.",
                file=sys.stderr,
            )
            return 1
        # Map args to what execute_coordinator_test expects
        args.repo_name = args.repo
        args.log_level = args.coordinator_log_level
        return execute_coordinator_test(args)
    else:
        # Validate run args
        if not args.all and not args.repo:
            print("Error: Either --all or --repo must be specified", file=sys.stderr)
            print(
                "Try 'mcp-coder coordinator --help' for more information.",
                file=sys.stderr,
            )
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
        return 1  # unreachable: argparse validates subcommand choices
    else:
        logger.debug("Check subcommand required")
        print(
            "Error: Please specify a check subcommand (e.g., 'branch-status', 'file-size')",
            file=sys.stderr,
        )
        print("Try 'mcp-coder check --help' for more information.", file=sys.stderr)
        return 1


def _handle_gh_tool_command(args: argparse.Namespace) -> int:
    """Handle gh-tool subcommands.

    Returns:
        Exit code from the executed gh-tool subcommand.
    """
    if hasattr(args, "gh_tool_subcommand") and args.gh_tool_subcommand:
        if args.gh_tool_subcommand == "get-base-branch":
            return execute_get_base_branch(args)
        elif args.gh_tool_subcommand == "define-labels":
            return execute_define_labels(args)
        elif args.gh_tool_subcommand == "issue-stats":
            return execute_coordinator_issue_stats(args)
        elif args.gh_tool_subcommand == "set-status":
            from .commands.set_status import execute_set_status

            return execute_set_status(args)
        elif args.gh_tool_subcommand == "checkout-issue-branch":
            return execute_checkout_issue_branch(args)
        return 1  # unreachable: argparse validates subcommand choices
    else:
        logger.debug("gh-tool subcommand required")
        print(
            "Error: Please specify a gh-tool subcommand"
            " (e.g., 'get-base-branch', 'define-labels', 'issue-stats',"
            " 'set-status', 'checkout-issue-branch')",
            file=sys.stderr,
        )
        print("Try 'mcp-coder gh-tool --help' for more information.", file=sys.stderr)
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
        return 1  # unreachable: argparse validates subcommand choices
    else:
        logger.debug("vscodeclaude subcommand required")
        print(
            "Error: Please specify a subcommand (e.g., 'launch', 'status')",
            file=sys.stderr,
        )
        print(
            "Try 'mcp-coder vscodeclaude --help' for more information.", file=sys.stderr
        )
        return 1


def _handle_git_tool_command(args: argparse.Namespace) -> int:
    """Handle git-tool subcommands.

    Returns:
        Exit code from the executed git-tool subcommand.
    """
    if hasattr(args, "git_tool_subcommand") and args.git_tool_subcommand:
        if args.git_tool_subcommand == "compact-diff":
            return execute_compact_diff(args)
        return 1  # unreachable: argparse validates subcommand choices
    else:
        logger.debug("git-tool subcommand required")
        print(
            "Error: Please specify a git-tool subcommand (e.g., 'compact-diff')",
            file=sys.stderr,
        )
        print("Try 'mcp-coder git-tool --help' for more information.", file=sys.stderr)
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
        logger.debug(f"Commit mode '{args.commit_mode}' not yet implemented")
        print(
            f"Error: Commit mode '{args.commit_mode}' is not yet implemented.",
            file=sys.stderr,
        )
        print("Try 'mcp-coder commit --help' for more information.", file=sys.stderr)
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

    # Initialize logging with resolved level
    log_level = _resolve_log_level(args)
    setup_logging(log_level)

    try:
        logger.debug(
            f"Starting mcp-coder CLI: command={args.command}, log_level={args.log_level}"
        )

        # Unified help: no command, "help" command, or --help flag
        if not args.command or args.command == "help" or args.help:
            help_text = get_help_text()
            print(help_text)
            return 0

        # Route to appropriate command handler
        if args.command == "init":
            return execute_init(args)
        elif args.command == "verify":
            return execute_verify(args)
        elif args.command == "prompt":
            return execute_prompt(args)
        elif args.command == "commit" and hasattr(args, "commit_mode"):
            return _handle_commit_command(args)
        elif args.command == "implement":
            return execute_implement(args)
        elif args.command == "icoder":
            return execute_icoder(args)
        elif args.command == "create-plan":
            return execute_create_plan(args)
        elif args.command == "create-pr":
            return execute_create_pr(args)
        elif args.command == "coordinator":
            return _handle_coordinator_command(args)
        elif args.command == "check":
            return _handle_check_command(args)
        elif args.command == "gh-tool":
            return _handle_gh_tool_command(args)
        elif args.command == "git-tool":
            return _handle_git_tool_command(args)
        elif args.command == "vscodeclaude":
            return _handle_vscodeclaude_command(args)

        return 1  # unreachable: argparse validates command choices

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
