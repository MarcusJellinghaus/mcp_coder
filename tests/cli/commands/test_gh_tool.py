"""Tests for gh-tool get-base-branch CLI command.

This module tests CLI-specific behavior (exit codes, output format, argument parsing).
Detection logic tests are in tests/workflow_utils/test_base_branch.py.
"""

import argparse
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.gh_tool import execute_get_base_branch

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_detect_base_branch() -> Generator[MagicMock, None, None]:
    """Mock detect_base_branch function."""
    with patch("mcp_coder.cli.commands.gh_tool.detect_base_branch") as mock:
        yield mock


@pytest.fixture
def mock_resolve_project_dir() -> Generator[MagicMock, None, None]:
    """Mock resolve_project_dir utility function."""
    with patch("mcp_coder.cli.commands.gh_tool.resolve_project_dir") as mock:
        yield mock


# ============================================================================
# Test Classes for Exit Codes
# ============================================================================


class TestGetBaseBranchExitCodes:
    """Tests for get-base-branch exit codes (0, 1, 2)."""

    def test_get_base_branch_exit_code_success(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 0 on successful detection."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "main"

    def test_get_base_branch_exit_code_detection_failure(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test exit code 1 when detection fails but no error occurred."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "unknown"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 1

    def test_get_base_branch_exit_code_error_not_git_repo(
        self,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 when not a git repository."""
        mock_resolve_project_dir.side_effect = ValueError("Not a git repository")

        args = argparse.Namespace(project_dir="/not/a/repo")
        result = execute_get_base_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_get_base_branch_exit_code_error_unexpected_exception(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 on unexpected exception."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.side_effect = Exception("Unexpected error")

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err


# ============================================================================
# Test Classes for Output Format
# ============================================================================


class TestGetBaseBranchOutputFormat:
    """Tests for get-base-branch output format (stdout only, no extra text)."""

    def test_get_base_branch_outputs_to_stdout(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that branch name is printed to stdout only."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "develop"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        # stdout should contain ONLY the branch name (and newline)
        assert captured.out.strip() == "develop"
        # stderr should be empty on success
        assert captured.err == ""

    def test_get_base_branch_no_extra_text_in_output(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that output contains only branch name without labels or prefixes."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "release/v2.1"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        captured = capsys.readouterr()
        # Should NOT contain labels like "Base branch:" or similar
        assert "Base" not in captured.out
        assert captured.out.strip() == "release/v2.1"


# ============================================================================
# Test Classes for CLI Integration
# ============================================================================


class TestGhToolCommandIntegration:
    """Test gh-tool command CLI integration."""

    def test_gh_tool_get_base_branch_command_exists(self) -> None:
        """Test that gh-tool get-base-branch is registered in CLI."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Check if gh-tool command exists in parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"

        subparser = subparsers_actions[0]
        assert "gh-tool" in subparser.choices, "gh-tool command should be registered"

    def test_gh_tool_help_shows_get_base_branch(self) -> None:
        """Test that gh-tool --help shows get-base-branch subcommand."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Get gh-tool subparser
        subparsers = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        gh_tool_parser = subparsers.choices["gh-tool"]

        # Get subcommands of gh-tool
        gh_tool_subparsers = [
            action
            for action in gh_tool_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert gh_tool_subparsers, "gh-tool should have subparsers"

        gh_tool_subcommands = gh_tool_subparsers[0]
        assert (
            "get-base-branch" in gh_tool_subcommands.choices
        ), "get-base-branch should be a subcommand of gh-tool"

    def test_gh_tool_get_base_branch_help_shows_exit_codes(self) -> None:
        """Test that get-base-branch --help shows exit codes in epilog."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Navigate to get-base-branch parser
        subparsers = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        gh_tool_parser = subparsers.choices["gh-tool"]

        gh_tool_subparsers = [
            action
            for action in gh_tool_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        get_base_branch_parser = gh_tool_subparsers.choices["get-base-branch"]

        # Check epilog contains exit code documentation
        epilog = get_base_branch_parser.epilog
        assert epilog is not None, "get-base-branch should have epilog"
        assert "0" in epilog, "Epilog should document exit code 0"
        assert "1" in epilog, "Epilog should document exit code 1"
        assert "2" in epilog, "Epilog should document exit code 2"

    def test_gh_tool_get_base_branch_command_calls_function(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test that gh-tool get-base-branch CLI command calls the execution function."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"

        # Create args as CLI parser would
        args = argparse.Namespace(project_dir=None)

        result = execute_get_base_branch(args)

        assert result == 0
        mock_detect_base_branch.assert_called_once_with(project_dir)

    def test_gh_tool_get_base_branch_with_project_dir_option(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test --project-dir option is parsed correctly."""
        custom_dir = Path("/custom/path")
        mock_resolve_project_dir.return_value = custom_dir
        mock_detect_base_branch.return_value = "develop"

        # Create args as CLI parser would with custom project_dir
        args = argparse.Namespace(project_dir="/custom/path")

        result = execute_get_base_branch(args)

        assert result == 0
        # Verify resolve_project_dir was called with the custom path
        mock_resolve_project_dir.assert_called_once_with("/custom/path")
        mock_detect_base_branch.assert_called_once_with(custom_dir)
