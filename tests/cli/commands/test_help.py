"""Tests for help command functionality."""

from mcp_coder.cli.command_catalog import (
    COMMAND_CATEGORIES,
    COMMAND_DESCRIPTIONS,
)
from mcp_coder.cli.commands.help import get_help_text

# --- Unified help output tests ---


def test_help_text_has_version_header() -> None:
    """Test help text includes version line."""
    output = get_help_text()
    # Version line should be present (mcp-coder X.Y.Z)
    lines = output.split("\n")
    version_lines = [
        line
        for line in lines
        if line.startswith("mcp-coder ")
        and line != "mcp-coder - AI-powered software development automation toolkit"
    ]
    assert len(version_lines) == 1, "Expected exactly one version line"


def test_help_text_has_options_section() -> None:
    """Test help text includes OPTIONS section with --version and --log-level."""
    output = get_help_text()
    assert "OPTIONS" in output
    assert "--version" in output
    assert "--log-level LEVEL" in output
    assert "Show version number" in output
    assert "DEBUG, INFO, WARNING, ERROR, CRITICAL" in output


def test_command_categories_contains_all_commands() -> None:
    """Test COMMAND_CATEGORIES has 4 categories with all expected commands."""
    assert len(COMMAND_CATEGORIES) == 4

    all_command_names = [name for _, names in COMMAND_CATEGORIES for name in names]

    expected_commands = [
        "init",
        "verify",
        "create-plan",
        "review-plan",
        "implement",
        "rebase",
        "review-implementation",
        "create-pr",
        "coordinator",
        "icoder",
        "vscodeclaude launch",
        "vscodeclaude status",
        "prompt",
        "commit auto",
        "check branch-status",
        "check file-size",
        "gh-tool checkout-issue-branch",
        "gh-tool set-status",
        "gh-tool get-base-branch",
        "gh-tool define-labels",
        "gh-tool issue-stats",
        "git-tool compact-diff",
    ]
    assert len(all_command_names) == 22
    for cmd in expected_commands:
        assert cmd in all_command_names, f"Missing command: {cmd}"

    # "help" should NOT be in the command list
    assert "help" not in all_command_names

    # TOOLS order matches the settled list.
    tools_names = next(names for title, names in COMMAND_CATEGORIES if title == "TOOLS")
    assert tools_names == [
        "prompt",
        "commit auto",
        "check branch-status",
        "check file-size",
        "gh-tool checkout-issue-branch",
        "gh-tool set-status",
        "gh-tool get-base-branch",
        "gh-tool define-labels",
        "gh-tool issue-stats",
        "git-tool compact-diff",
    ]


def test_help_text_has_all_category_headers() -> None:
    """Test help output contains all category headers."""
    output = get_help_text()
    assert "SETUP" in output
    assert "BACKGROUND DEVELOPMENT" in output
    assert "INTERACTIVE DEVELOPMENT" in output
    assert "TOOLS" in output


def test_help_text_has_all_commands() -> None:
    """Test help output contains every command name and its description."""
    output = get_help_text()
    for name, description in COMMAND_DESCRIPTIONS.items():
        assert name in output, f"Missing command in output: {name}"
        assert description in output, f"Missing description in output: {description}"


def test_help_text_command_column_alignment() -> None:
    """Test all command description columns start at the same position."""
    output = get_help_text()
    all_command_names = [name for _, names in COMMAND_CATEGORIES for name in names]
    max_width = max(len(name) for name in all_command_names)
    expected_col = 2 + max_width + 2  # "  " + padded name + "  "

    # Find command lines (indented with 2 spaces, contain a known command name)
    command_lines = [
        line
        for line in output.split("\n")
        if line.startswith("  ")
        and line.strip()
        and any(cmd_name in line for cmd_name in all_command_names)
    ]
    assert len(command_lines) > 0, "No command lines found"

    for line in command_lines:
        assert len(line) > expected_col, f"Line too short: {line!r}"
        desc_char = line[expected_col]
        assert (
            desc_char != " "
        ), f"Description not aligned at column {expected_col}: {line!r}"


def test_help_text_has_usage_line() -> None:
    """Test help text contains the usage line."""
    output = get_help_text()
    assert "Usage: mcp-coder <command> [options]" in output


def test_help_text_has_footer() -> None:
    """Test help text contains the footer."""
    output = get_help_text()
    assert "Run 'mcp-coder <command> --help' for command-specific options." in output


def test_help_text_no_github_url() -> None:
    """Test help text does not contain GitHub URL."""
    output = get_help_text()
    assert "github.com" not in output


def test_help_text_has_header() -> None:
    """Test help text contains the header."""
    output = get_help_text()
    assert "mcp-coder - AI-powered software development automation toolkit" in output
