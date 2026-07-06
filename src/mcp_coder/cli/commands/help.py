"""Help commands for the MCP Coder CLI."""

from ... import __version__
from ..command_catalog import COMMAND_CATEGORIES, COMMAND_DESCRIPTIONS


def _render_help() -> str:
    """Render help text from the command catalog.

    Returns:
        Formatted help text with version header and OPTIONS section.
    """
    max_width = max(len(name) for _, names in COMMAND_CATEGORIES for name in names)
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
    for title, names in COMMAND_CATEGORIES:
        lines.append("")
        lines.append(title)
        for name in names:
            lines.append(f"  {name:<{max_width}}  {COMMAND_DESCRIPTIONS[name]}")
    lines.append("")
    lines.append("Run 'mcp-coder <command> --help' for command-specific options.")
    return "\n".join(lines)


def get_help_text() -> str:
    """Render unified help text with version, options, and categorized commands.

    Returns:
        Formatted help text.
    """
    return _render_help()
