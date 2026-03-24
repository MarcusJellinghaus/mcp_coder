"""Help commands for the MCP Coder CLI."""

import argparse
import logging
from typing import NamedTuple

logger = logging.getLogger(__name__)


class Command(NamedTuple):
    name: str
    description: str


class Category(NamedTuple):
    name: str
    description: str
    commands: list[Command]


COMMAND_CATEGORIES: list[Category] = [
    Category(
        name="SETUP",
        description="Configure your project and verify the environment.",
        commands=[
            Command("init", "Create default configuration file"),
            Command("verify", "Verify CLI installation and configuration"),
            Command("define-labels", "Sync workflow status labels to GitHub"),
        ],
    ),
    Category(
        name="BACKGROUND DEVELOPMENT",
        description="Plan, implement, and create PRs for GitHub issues.",
        commands=[
            Command("create-plan", "Generate implementation plan for a GitHub issue"),
            Command("implement", "Execute implementation workflow"),
            Command("create-pr", "Create pull request with AI-generated summary"),
        ],
    ),
    Category(
        name="COORDINATION",
        description="Orchestrate workflows across repositories.",
        commands=[
            Command("coordinator test", "Trigger integration test"),
            Command("coordinator run", "Monitor and dispatch workflows"),
            Command("coordinator vscodeclaude", "Manage VSCode/Claude sessions"),
            Command(
                "coordinator vscodeclaude status",
                "Show issue and VSCode/Claude session status",
            ),
            Command("coordinator issue-stats", "Display issue statistics"),
        ],
    ),
    Category(
        name="TOOLS",
        description="Day-to-day development utilities.",
        commands=[
            Command("prompt", "Execute prompt via Claude API"),
            Command("commit auto", "Auto-generate commit message"),
            Command("commit clipboard", "Use clipboard commit message"),
            Command("set-status", "Update GitHub issue workflow status label"),
            Command("check branch-status", "Check branch readiness status"),
            Command("check file-size", "Check file sizes against maximum"),
            Command("gh-tool get-base-branch", "Detect base branch for feature branch"),
            Command("git-tool compact-diff", "Generate compact diff"),
        ],
    ),
]


def get_compact_help_text() -> str:
    """Render compact help: category headers + aligned commands."""
    max_width = max(len(cmd.name) for cat in COMMAND_CATEGORIES for cmd in cat.commands)
    lines = [
        "mcp-coder - AI-powered software development automation toolkit",
        "",
        "Usage: mcp-coder <command> [options]",
    ]
    for cat in COMMAND_CATEGORIES:
        lines.append("")
        lines.append(cat.name)
        for cmd in cat.commands:
            lines.append(f"  {cmd.name:<{max_width}}  {cmd.description}")
    lines.append("")
    lines.append("Run 'mcp-coder help' for detailed usage.")
    lines.append("Run 'mcp-coder <command> --help' for command-specific options.")
    return "\n".join(lines)


def execute_help(_args: argparse.Namespace) -> int:
    """Execute help command.

    Returns:
        Exit code (0 for success).
    """
    logger.info("Executing help command")

    help_text = get_help_text(include_examples=True)
    print(help_text)

    logger.info("Help command completed successfully")
    return 0


def get_help_text(include_examples: bool = False) -> str:
    """Get comprehensive help text for all commands.

    Args:
        include_examples: If True, include usage examples section

    Returns:
        Formatted help text string containing all command descriptions.
    """
    examples = get_usage_examples() if include_examples else ""
    help_content = f"""MCP Coder - AI-powered software development automation toolkit

USAGE:
    mcp-coder <command> [options]

COMMANDS:
    help                    Show help information
    init                    Create default configuration file
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
                           --llm-method METHOD    claude (default) | langchain

    commit auto             Auto-generate commit message using LLM
    commit auto --preview   Show generated message and ask for confirmation
    commit auto --llm-method METHOD   LLM provider (default: claude)
    commit clipboard        Use commit message from clipboard

    define-labels           Sync workflow status labels to GitHub repository
                           --project-dir PATH    Project directory (default: current)
                           --dry-run             Preview changes without applying

{examples}

For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder"""

    return help_content


def get_usage_examples() -> str:
    """Get usage examples for common workflows.

    Returns:
        Formatted string containing example CLI commands and usage patterns.
    """
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
