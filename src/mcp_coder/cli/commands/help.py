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

    help_text = get_help_text()
    print(help_text)

    logger.info("Help command completed successfully")
    return 0


def get_help_text() -> str:
    """Render detailed help: category headers + descriptions + aligned commands."""
    max_width = max(len(cmd.name) for cat in COMMAND_CATEGORIES for cmd in cat.commands)
    lines = [
        "mcp-coder - AI-powered software development automation toolkit",
        "",
        "Usage: mcp-coder <command> [options]",
    ]
    for cat in COMMAND_CATEGORIES:
        lines.append("")
        lines.append(cat.name)
        lines.append(f"  {cat.description}")
        lines.append("")
        for cmd in cat.commands:
            lines.append(f"  {cmd.name:<{max_width}}  {cmd.description}")
    lines.append("")
    lines.append("Run 'mcp-coder <command> --help' for command-specific options.")
    lines.append("")
    lines.append(
        "For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder"
    )
    return "\n".join(lines)
