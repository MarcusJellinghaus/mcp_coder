"""Tests for help command functionality."""

import argparse
import sys
from io import StringIO

import pytest

from src.mcp_coder.cli.commands.help import (
    execute_help,
    get_help_text,
    get_usage_examples,
)


def test_execute_help_returns_success(capsys) -> None:
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
    help_text = get_help_text()

    assert "MCP Coder - AI-powered software development automation toolkit" in help_text
    assert "USAGE:" in help_text
    assert "COMMANDS:" in help_text
    assert "help" in help_text
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


def test_help_text_formatting() -> None:
    """Test help text is properly formatted."""
    help_text = get_help_text()

    # Check that the help text has proper structure
    lines = help_text.split("\n")
    assert len(lines) > 5  # Should have multiple lines

    # Check for proper sections
    assert any("USAGE:" in line for line in lines)
    assert any("COMMANDS:" in line for line in lines)
    assert any("EXAMPLES:" in line for line in lines)


def test_help_text_consistency() -> None:
    """Test that help text is consistent with examples."""
    help_text = get_help_text()
    examples = get_usage_examples()

    # Examples should be included in help text
    assert examples in help_text
