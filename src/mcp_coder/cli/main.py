"""Main CLI entry point for MCP Coder."""
import argparse
import logging
import sys
from pathlib import Path

from ..log_utils import setup_logging

# Initialize logging
setup_logging("INFO")
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
    
    # Add subparsers for future commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND",
    )
    
    # Placeholder for future commands - will be populated in later steps
    # help command - Step 2
    # commit auto command - Step 5  
    # commit clipboard command - Step 6
    
    return parser


def handle_no_command(args: argparse.Namespace) -> int:
    """Handle case when no command is provided."""
    logger.info("No command provided, showing help")
    print("mcp-coder: AI-powered software development automation toolkit")
    print("")
    print("Usage: mcp-coder COMMAND [OPTIONS]")
    print("")
    print("Available commands:")
    print("  help                    Show detailed help information")
    print("  commit auto             Auto-generate and create commit")
    print("  commit clipboard        Commit using message from clipboard")
    print("")
    print("For more information, run: mcp-coder help")
    print("Or visit: https://github.com/MarcusJellinghaus/mcp_coder")
    
    return 1  # Exit with error code since no command was provided


def main() -> int:
    """Main CLI entry point. Returns exit code."""
    try:
        logger.info("Starting mcp-coder CLI")
        
        parser = create_parser()
        args = parser.parse_args()
        
        logger.info(f"Parsed arguments: command={args.command}")
        
        # Handle case when no command is provided
        if not args.command:
            return handle_no_command(args)
        
        # Route to appropriate command handler
        # This will be implemented in later steps
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
