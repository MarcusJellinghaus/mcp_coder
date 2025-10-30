"""Main CLI entry point for MCP Coder."""

import argparse
import logging
import sys

from ..utils.log_utils import setup_logging
from .commands.commit import execute_commit_auto, execute_commit_clipboard
from .commands.coordinator import execute_coordinator_run, execute_coordinator_test
from .commands.create_plan import execute_create_plan
from .commands.create_pr import execute_create_pr
from .commands.help import execute_help, get_help_text
from .commands.implement import execute_implement
from .commands.prompt import execute_prompt
from .commands.verify import execute_verify

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
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
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
        default="claude_code_cli",
        metavar="METHOD",
        help="Communication method: claude_code_cli (default) or claude_code_api",
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
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    auto_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )

    # commit clipboard command - Step 6
    clipboard_parser = commit_subparsers.add_parser(
        "clipboard", help="Use commit message from clipboard"
    )
    clipboard_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
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

    # Create plan command - Generate implementation plan from GitHub issue
    create_plan_parser = subparsers.add_parser(
        "create-plan", help="Generate implementation plan for a GitHub issue"
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

    # Create PR command - Step 3
    create_pr_parser = subparsers.add_parser(
        "create-pr", help="Create pull request with AI-generated summary"
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

    # Coordinator commands - Jenkins-based integration testing
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
        "test", help="Trigger Jenkins integration test for repository"
    )
    test_parser.add_argument(
        "repo_name", help="Repository name from config (e.g., mcp_coder)"
    )
    test_parser.add_argument(
        "--branch-name",
        required=True,
        help="Git branch to test (e.g., feature-x, main)",
    )

    # coordinator run command
    run_parser = coordinator_subparsers.add_parser(
        "run", help="Monitor and dispatch workflows for GitHub issues"
    )

    # Mutually exclusive group: --all OR --repo (one required)
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
        logger.info(
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
            if args.commit_mode == "auto":
                return execute_commit_auto(args)
            elif args.commit_mode == "clipboard":
                return execute_commit_clipboard(args)
            else:
                logger.error(f"Commit mode '{args.commit_mode}' not yet implemented")
                print(
                    f"Error: Commit mode '{args.commit_mode}' is not yet implemented."
                )
                return 1
        elif args.command == "implement":
            return execute_implement(args)
        elif args.command == "create-plan":
            return execute_create_plan(args)
        elif args.command == "create-pr":
            return execute_create_pr(args)
        elif args.command == "coordinator":
            if hasattr(args, "coordinator_subcommand") and args.coordinator_subcommand:
                if args.coordinator_subcommand == "test":
                    return execute_coordinator_test(args)
                elif args.coordinator_subcommand == "run":
                    return execute_coordinator_run(args)
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
                print(
                    "Error: Please specify a coordinator subcommand (e.g., 'test', 'run')"
                )
                return 1

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
