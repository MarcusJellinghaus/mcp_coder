"""Tests for help command functionality."""

import argparse

import pytest

from mcp_coder.cli.commands.help import (
    COMMAND_CATEGORIES,
    execute_help,
    get_compact_help_text,
    get_help_text,
)


def test_execute_help_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test help command returns exit code 0."""
    args = argparse.Namespace(command="help")

    result = execute_help(args)

    assert result == 0
    captured = capsys.readouterr()
    assert (
        "mcp-coder - AI-powered software development automation toolkit" in captured.out
    )


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
        assert len(line) > expected_col, f"Line too short: {line!r}"
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


# --- Step 2: Detailed help (get_help_text) tests ---


def test_detailed_help_has_category_descriptions() -> None:
    """Test detailed help output contains all 4 category description strings."""
    output = get_help_text()
    for cat in COMMAND_CATEGORIES:
        assert (
            cat.description in output
        ), f"Missing category description: {cat.description}"


def test_detailed_help_has_all_category_headers() -> None:
    """Test detailed help output contains all category headers."""
    output = get_help_text()
    assert "SETUP" in output
    assert "BACKGROUND DEVELOPMENT" in output
    assert "COORDINATION" in output
    assert "TOOLS" in output


def test_detailed_help_has_all_commands() -> None:
    """Test detailed help output contains all command names."""
    output = get_help_text()
    for cat in COMMAND_CATEGORIES:
        for cmd in cat.commands:
            assert cmd.name in output, f"Missing command in output: {cmd.name}"


def test_detailed_help_column_alignment() -> None:
    """Test all description columns in detailed help start at the same position."""
    output = get_help_text()
    max_width = max(len(cmd.name) for cat in COMMAND_CATEGORIES for cmd in cat.commands)
    expected_col = 2 + max_width + 2  # "  " + padded name + "  "

    # Find command lines: indented with 2 spaces, contain a command name
    all_command_names = {cmd.name for cat in COMMAND_CATEGORIES for cmd in cat.commands}
    command_lines = [
        line
        for line in output.split("\n")
        if line.startswith("  ")
        and line.strip()
        and any(cmd_name in line for cmd_name in all_command_names)
        and line.strip() not in {cat.description for cat in COMMAND_CATEGORIES}
    ]
    assert len(command_lines) > 0, "No command lines found"

    for line in command_lines:
        assert len(line) > expected_col, f"Line too short: {line!r}"
        desc_char = line[expected_col]
        assert (
            desc_char != " "
        ), f"Description not aligned at column {expected_col}: {line!r}"


def test_detailed_help_has_footer() -> None:
    """Test detailed help contains the footer lines."""
    output = get_help_text()
    assert "Run 'mcp-coder <command> --help' for command-specific options." in output
    assert (
        "For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder"
        in output
    )


def test_detailed_help_has_usage_line() -> None:
    """Test detailed help contains the usage line."""
    output = get_help_text()
    assert "Usage: mcp-coder <command> [options]" in output


def test_detailed_help_has_header() -> None:
    """Test detailed help contains the header."""
    output = get_help_text()
    assert "mcp-coder - AI-powered software development automation toolkit" in output
