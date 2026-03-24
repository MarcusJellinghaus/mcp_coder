"""Tests for help command functionality."""

import argparse
import sys
from io import StringIO

import pytest

from mcp_coder.cli.commands.help import (
    COMMAND_CATEGORIES,
    execute_help,
    get_compact_help_text,
    get_help_text,
    get_usage_examples,
)


def test_execute_help_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test help command returns exit code 0."""
    args = argparse.Namespace(command="help")

    result = execute_help(args)

    assert result == 0
    captured = capsys.readouterr()
    assert (
        "MCP Coder - AI-powered software development automation toolkit" in captured.out
    )


def test_get_help_text_contains_all_commands() -> None:
    """Test help text includes all available commands."""
    help_text = get_help_text(include_examples=True)

    assert "MCP Coder - AI-powered software development automation toolkit" in help_text
    assert "USAGE:" in help_text
    assert "COMMANDS:" in help_text
    assert "help" in help_text
    assert "init" in help_text
    assert "Create default configuration file" in help_text
    assert "commit auto" in help_text
    assert "commit clipboard" in help_text
    assert "EXAMPLES:" in help_text
    assert "https://github.com/MarcusJellinghaus/mcp_coder" in help_text


def test_get_usage_examples_has_examples() -> None:
    """Test usage examples are provided."""
    examples = get_usage_examples()

    assert "EXAMPLES:" in examples
    assert "mcp-coder help" in examples
    assert "mcp-coder commit auto" in examples
    assert "mcp-coder commit clipboard" in examples


def test_get_help_text_without_examples() -> None:
    """Test help text without examples doesn't include examples section."""
    help_text = get_help_text(include_examples=False)

    assert "MCP Coder - AI-powered software development automation toolkit" in help_text
    assert "USAGE:" in help_text
    assert "COMMANDS:" in help_text
    assert "help" in help_text
    assert "commit auto" in help_text
    assert "commit clipboard" in help_text
    assert "EXAMPLES:" not in help_text  # Should not include examples
    assert "https://github.com/MarcusJellinghaus/mcp_coder" in help_text


def test_help_text_formatting() -> None:
    """Test help text is properly formatted."""
    help_text = get_help_text(include_examples=True)

    # Check that the help text has proper structure
    lines = help_text.split("\n")
    assert len(lines) > 5  # Should have multiple lines

    # Check for proper sections
    assert any("USAGE:" in line for line in lines)
    assert any("COMMANDS:" in line for line in lines)
    assert any("EXAMPLES:" in line for line in lines)


def test_help_text_consistency() -> None:
    """Test that help text is consistent with examples."""
    help_text = get_help_text(include_examples=True)
    examples = get_usage_examples()

    # Examples should be included in help text
    assert examples in help_text


# --- Step 1: Data structure and compact help tests ---


def test_command_categories_contains_all_commands() -> None:
    """Test COMMAND_CATEGORIES has 4 categories with all expected commands."""
    assert len(COMMAND_CATEGORIES) == 4

    all_command_names = [cmd.name for cat in COMMAND_CATEGORIES for cmd in cat.commands]

    expected_commands = [
        "init",
        "verify",
        "define-labels",
        "create-plan",
        "implement",
        "create-pr",
        "coordinator test",
        "coordinator run",
        "coordinator vscodeclaude",
        "coordinator vscodeclaude status",
        "coordinator issue-stats",
        "prompt",
        "commit auto",
        "commit clipboard",
        "set-status",
        "check branch-status",
        "check file-size",
        "gh-tool get-base-branch",
        "git-tool compact-diff",
    ]
    for cmd in expected_commands:
        assert cmd in all_command_names, f"Missing command: {cmd}"


def test_compact_help_has_all_category_headers() -> None:
    """Test compact help output contains all category headers."""
    output = get_compact_help_text()
    assert "SETUP" in output
    assert "BACKGROUND DEVELOPMENT" in output
    assert "COORDINATION" in output
    assert "TOOLS" in output


def test_compact_help_has_all_commands() -> None:
    """Test compact help output contains every command name."""
    output = get_compact_help_text()
    for cat in COMMAND_CATEGORIES:
        for cmd in cat.commands:
            assert cmd.name in output, f"Missing command in output: {cmd.name}"


def test_compact_help_no_category_descriptions() -> None:
    """Test compact help does NOT contain category description strings."""
    output = get_compact_help_text()
    for cat in COMMAND_CATEGORIES:
        assert (
            cat.description not in output
        ), f"Category description should not appear: {cat.description}"


def test_compact_help_column_alignment() -> None:
    """Test all description columns start at the same position."""
    output = get_compact_help_text()
    # Compute expected alignment from data
    max_width = max(len(cmd.name) for cat in COMMAND_CATEGORIES for cmd in cat.commands)
    expected_col = 2 + max_width + 2  # "  " + padded name + "  "

    # Find command lines (indented with 2 spaces, not category headers)
    command_lines = [
        line
        for line in output.split("\n")
        if line.startswith("  ") and line.strip() and not line.strip().isupper()
    ]
    assert len(command_lines) > 0, "No command lines found"

    for line in command_lines:
        # Description should start at expected_col
        desc_char = line[expected_col]
        assert (
            desc_char != " "
        ), f"Description not aligned at column {expected_col}: {line!r}"


def test_compact_help_has_usage_line() -> None:
    """Test compact help contains the usage line."""
    output = get_compact_help_text()
    assert "Usage: mcp-coder <command> [options]" in output


def test_compact_help_has_footer() -> None:
    """Test compact help contains the footer."""
    output = get_compact_help_text()
    assert "Run 'mcp-coder help' for detailed usage." in output


def test_prompt_command_documentation() -> None:
    """Test that prompt command is fully documented with all features."""
    help_text = get_help_text(include_examples=True)
    examples = get_usage_examples()

    # Check command is listed
    assert "prompt <text>" in help_text
    assert "Execute prompt via Claude API with configurable debug output" in help_text

    # Check that the detailed parameter documentation is present
    assert "--verbosity LEVEL" in help_text
    assert "--store-response" in help_text
    assert "--continue-from FILE" in help_text

    # Check verbosity level descriptions
    assert "just-text (default)" in help_text
    assert "verbose: + tool interactions + performance metrics" in help_text
    assert "raw: + complete JSON structures + API responses" in help_text

    # Check all verbosity levels are documented in examples
    assert "--verbosity verbose" in examples
    assert "--verbosity raw" in examples
    assert "just-text" in examples

    # Check storage functionality is documented
    assert "--store-response" in examples
    assert "--continue-from" in examples

    # Check various usage patterns are shown
    assert 'mcp-coder prompt "What is Python?"' in examples
    assert 'mcp-coder prompt "Debug this error" --verbosity verbose' in examples
    assert 'mcp-coder prompt "Debug this error" --verbosity raw' in examples
    assert "response_2025-09-19T14-30-22.json" in examples
