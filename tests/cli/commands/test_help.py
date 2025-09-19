"""Tests for help command functionality."""

import argparse
import sys
from io import StringIO

import pytest

from mcp_coder.cli.commands.help import (
    execute_help,
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


def test_prompt_command_documentation() -> None:
    """Test that prompt command is fully documented with all features."""
    help_text = get_help_text()
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
