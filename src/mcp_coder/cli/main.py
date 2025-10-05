"""Main CLI entry point for MCP Coder."""

import argparse
import logging
import sys

from ..utils.log_utils import setup_logging
from .commands.help import get_help_text

# Logger will be initialized in main()
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-coder",
        description="AI-powered software development automation toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-coder help                    Show detailed help information
  mcp-coder commit auto             Auto-generate and create commit
  mcp-coder commit clipboard        Commit using message from clipboard

For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Set the logging level (default: WARNING)",
        metavar="LEVEL",
    )

    # Add subparsers for future commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND",
    )

    # Help command - Step 2
    help_parser = subparsers.add_parser("help", help="Show help information")

    # Verify command - Claude installation verification
    verify_parser = subparsers.add_parser(
        "verify", help="Verify Claude CLI installation and configuration"
    )

    # Prompt command - Execute prompt via Claude API with configurable debug output
    prompt_parser = subparsers.add_parser(
        "prompt", help="Execute prompt via Claude API with configurable debug output"
    )
    prompt_parser.add_argument("prompt", help="The prompt to send to Claude")
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

    # Session continuation options (mutually exclusive with each other, but --session-id has priority)
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
        default="claude_code_api",
        metavar="METHOD",
        help="Communication method: claude_code_api (default) or claude_code_cli",
    )
    prompt_parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        metavar="FORMAT",
        help="Output format: text (default) or json (includes session_id)",
    )

    # Commit commands - Step 5
    commit_parser = subparsers.add_parser("commit", help="Git commit operations")
    commit_subparsers = commit_parser.add_subparsers(
        dest="commit_mode", help="Available commit modes", metavar="MODE"
    )

    # commit auto command - Step 5
    auto_parser = commit_subparsers.add_parser(
        "auto", help="Auto-generate commit message using LLM"
    )
    auto_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show generated message and ask for confirmation before committing",
    )
    auto_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_api",
        help="LLM method to use (default: claude_code_api)",
    )

    # commit clipboard command - Step 6
    clipboard_parser = commit_subparsers.add_parser(
        "clipboard", help="Use commit message from clipboard"
    )

    # Implement command - Step 5
    implement_parser = subparsers.add_parser(
        "implement", help="Execute implementation workflow from task tracker"
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

    return parser


def handle_no_command(args: argparse.Namespace) -> int:
    """Handle case when no command is provided."""
    logger.info("No command provided, showing help")

    help_text = get_help_text(include_examples=False)
    print(help_text)

    return 1  # Exit with error code since no command was provided


def main() -> int:
    """Main CLI entry point. Returns exit code."""
    # Parse arguments first to get log level
    parser = create_parser()
    args = parser.parse_args()

    # Initialize logging with user-specified level
    setup_logging(args.log_level)

    try:
        logger.info("Starting mcp-coder CLI")
        logger.info(
            f"Parsed arguments: command={args.command}, log_level={args.log_level}"
        )

        # Handle case when no command is provided
        if not args.command:
            return handle_no_command(args)

        # Route to appropriate command handler
        if args.command == "help":
            from .commands.help import execute_help
            return execute_help(args)
        elif args.command == "verify":
            from .commands.verify import execute_verify
            return execute_verify(args)
        elif args.command == "prompt":
            from .commands.prompt import execute_prompt
            return execute_prompt(args)
        elif args.command == "commit" and hasattr(args, "commit_mode"):
            if args.commit_mode == "auto":
                from .commands.commit import execute_commit_auto
                return execute_commit_auto(args)
            elif args.commit_mode == "clipboard":
                from .commands.commit import execute_commit_clipboard
                return execute_commit_clipboard(args)
            else:
                logger.error(f"Commit mode '{args.commit_mode}' not yet implemented")
                print(
                    f"Error: Commit mode '{args.commit_mode}' is not yet implemented."
                )
                return 1
        elif args.command == "implement":
            from .commands.implement import execute_implement
            return execute_implement(args)

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
