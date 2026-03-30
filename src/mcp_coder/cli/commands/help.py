"""Help commands for the MCP Coder CLI."""

from typing import NamedTuple

from ... import __version__


class Command(NamedTuple):
    """A CLI command with a name and description."""

    name: str
    description: str


class Category(NamedTuple):
    """A group of related CLI commands."""

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
        ],
    ),
    Category(
        name="BACKGROUND DEVELOPMENT",
        description="Plan, implement, and create PRs for GitHub issues.",
        commands=[
            Command("create-plan", "Generate implementation plan for a GitHub issue"),
            Command("implement", "Execute implementation workflow"),
            Command("create-pr", "Create pull request with AI-generated summary"),
            Command(
                "coordinator", "Monitor and dispatch workflows across repositories"
            ),
        ],
    ),
    Category(
        name="INTERACTIVE DEVELOPMENT",
        description="Interactive coding tools and local workspace management.",
        commands=[
            Command("icoder", "Interactive terminal chat for LLM-assisted coding"),
            Command("vscodeclaude launch", "Launch VSCode/Claude session for issues"),
            Command("vscodeclaude status", "Show current VSCode/Claude sessions"),
        ],
    ),
    Category(
        name="TOOLS",
        description="Day-to-day development utilities.",
        commands=[
            Command("prompt", "Execute prompt via Claude API"),
            Command("commit auto", "Auto-generate commit message"),
            Command("commit clipboard", "Use clipboard commit message"),
            Command("check branch-status", "Check branch readiness status"),
            Command("check file-size", "Check file sizes against maximum"),
            Command("gh-tool set-status", "Update GitHub issue workflow status label"),
            Command("gh-tool define-labels", "Sync workflow status labels to GitHub"),
            Command("gh-tool issue-stats", "Display issue statistics"),
            Command("gh-tool get-base-branch", "Detect base branch for feature branch"),
            Command("git-tool compact-diff", "Generate compact diff"),
        ],
    ),
]


def _render_help() -> str:
    """Render help text from COMMAND_CATEGORIES.

    Returns:
        Formatted help text with version header and OPTIONS section.
    """
    max_width = max(len(cmd.name) for cat in COMMAND_CATEGORIES for cmd in cat.commands)
    option_width = max_width  # align OPTIONS section with commands
    lines = [
        "mcp-coder - AI-powered software development automation toolkit",
        f"mcp-coder {__version__}",
        "",
        "Usage: mcp-coder <command> [options]",
        "",
        "OPTIONS",
        f"  {'--version':<{option_width}}  Show version number",
        f"  {'--log-level LEVEL':<{option_width}}  Set logging level"
        " (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ]
    for cat in COMMAND_CATEGORIES:
        lines.append("")
        lines.append(cat.name)
        for cmd in cat.commands:
            lines.append(f"  {cmd.name:<{max_width}}  {cmd.description}")
    lines.append("")
    lines.append("Run 'mcp-coder <command> --help' for command-specific options.")
    return "\n".join(lines)


def get_help_text() -> str:
    """Render unified help text with version, options, and categorized commands.

    Returns:
        Formatted help text.
    """
    return _render_help()
