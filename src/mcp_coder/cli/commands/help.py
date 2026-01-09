"""Help commands for the MCP Coder CLI."""

import argparse
import logging

logger = logging.getLogger(__name__)


def execute_help(args: argparse.Namespace) -> int:
    """Execute help command. Returns exit code."""
    logger.info("Executing help command")

    help_text = get_help_text(include_examples=True)
    print(help_text)

    logger.info("Help command completed successfully")
    return 0


def get_help_text(include_examples: bool = False) -> str:
    """Get comprehensive help text for all commands.

    Args:
        include_examples: If True, include usage examples section
    """
    examples = get_usage_examples() if include_examples else ""
    help_content = f"""MCP Coder - AI-powered software development automation toolkit

USAGE:
    mcp-coder <command> [options]

COMMANDS:
    help                    Show help information
    verify                  Verify Claude CLI installation and configuration
    prompt <text>           Execute prompt via Claude API with configurable debug output

                           Output Control:
                           --verbosity LEVEL      just-text (default) | verbose: + tool interactions + performance metrics | raw: + complete JSON structures + API responses
                           --output-format        text (default) | json (includes session_id)

                           Session Continuation (Priority: --session-id > --continue-session-from > --continue-session):
                           --session-id ID                Direct session ID for resuming conversation
                           --continue-session-from FILE   Resume from specific stored session file
                           --continue-from FILE           Alias for --continue-session-from
                           --continue-session             Resume from most recent session (auto-discovers)
                           --store-response               Save session to .mcp-coder/responses/ for later use

                           Configuration:
                           --timeout SECONDS      API timeout in seconds (default: 60)
                           --llm-method METHOD    claude_code_api (default) | claude_code_cli

    commit auto             Auto-generate commit message using LLM
    commit auto --preview   Show generated message and ask for confirmation
    commit auto --llm-method METHOD   Communication method (default: claude_code_api)
    commit clipboard        Use commit message from clipboard

    define-labels           Sync workflow status labels to GitHub repository
                           --project-dir PATH    Project directory (default: current)
                           --dry-run             Preview changes without applying

{examples}

For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder"""

    return help_content


def get_usage_examples() -> str:
    """Get usage examples for common workflows."""
    return """EXAMPLES:
    mcp-coder help                    # Show this help
    mcp-coder verify                  # Check Claude CLI installation
    
    # Basic prompt usage (default just-text output)
    mcp-coder prompt "What is Python?"
    mcp-coder prompt "Explain how async/await works"
    
    # Verbosity levels:
    mcp-coder prompt "Debug this error" --verbosity just-text     # Default: response + tool summary
    mcp-coder prompt "Debug this error" --verbosity verbose       # + performance metrics + session info
    mcp-coder prompt "Debug this error" --verbosity raw           # + complete JSON + API responses

    # Timeout control:
    mcp-coder prompt "Complex analysis" --timeout 120             # 2 minute timeout for complex requests
    mcp-coder prompt "Quick question" --timeout 30               # 30 second timeout for simple requests
    
    # Session storage and continuation:
    mcp-coder prompt "Start project planning" --store-response                      # Save session
    mcp-coder prompt "What's next?" --continue-from response_2025-09-19T14-30-22.json # Continue conversation
    mcp-coder prompt "What's next?" --continue                                      # Continue from most recent session
    
    # Combined usage for complex workflows:
    mcp-coder prompt "Complex analysis" --verbosity verbose --store-response         # Debug + save
    
    # Commit command examples
    mcp-coder commit auto             # Analyze changes and auto-commit
    mcp-coder commit auto --preview   # Review generated message before commit
    mcp-coder commit clipboard        # Commit with clipboard message"""
