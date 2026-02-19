"""Tests for git-tool compact-diff CLI command.

This module tests CLI-specific behavior (exit codes, output format, argument parsing).
Core compact diff logic tests are in tests/utils/git_operations/test_compact_diffs.py.
"""

import argparse
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.git_tool import execute_compact_diff

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_get_compact_diff() -> Generator[MagicMock, None, None]:
    """Mock get_compact_diff function."""
    with patch("mcp_coder.cli.commands.git_tool.get_compact_diff") as mock:
        yield mock


@pytest.fixture
def mock_detect_base_branch() -> Generator[MagicMock, None, None]:
    """Mock detect_base_branch function."""
    with patch("mcp_coder.cli.commands.git_tool.detect_base_branch") as mock:
        yield mock


@pytest.fixture
def mock_resolve_project_dir() -> Generator[MagicMock, None, None]:
    """Mock resolve_project_dir utility function."""
    with patch("mcp_coder.cli.commands.git_tool.resolve_project_dir") as mock:
        yield mock


# ============================================================================
# Test Classes for Exit Codes
# ============================================================================


class TestCompactDiffExitCodes:
    """Test exit codes 0, 1, 2."""

    def test_exit_code_success(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 0 on success."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff output here"

        args = argparse.Namespace(project_dir=None, base_branch=None, exclude=None)
        result = execute_compact_diff(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "diff output here" in captured.out

    def test_exit_code_no_base_branch(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 1 when detect_base_branch returns None."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = None

        args = argparse.Namespace(project_dir=None, base_branch=None, exclude=None)
        result = execute_compact_diff(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_exit_code_invalid_repo(
        self,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 when resolve_project_dir raises ValueError."""
        mock_resolve_project_dir.side_effect = ValueError("Not a git repository")

        args = argparse.Namespace(
            project_dir="/not/a/repo", base_branch=None, exclude=None
        )
        result = execute_compact_diff(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_exit_code_unexpected_exception(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 on unexpected exception from get_compact_diff."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.side_effect = Exception("Unexpected error")

        args = argparse.Namespace(project_dir=None, base_branch=None, exclude=None)
        result = execute_compact_diff(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err


# ============================================================================
# Test Classes for Output Format
# ============================================================================


class TestCompactDiffOutputFormat:
    """Test stdout/stderr separation."""

    def test_diff_printed_to_stdout(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that compact diff text is written to stdout."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        diff_text = "diff --git a/foo.py b/foo.py\n+new line"
        mock_get_compact_diff.return_value = diff_text

        args = argparse.Namespace(project_dir=None, base_branch=None, exclude=None)
        result = execute_compact_diff(args)

        assert result == 0
        captured = capsys.readouterr()
        assert diff_text in captured.out
        assert captured.err == ""

    def test_no_extra_text_in_output(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that stdout contains exactly the diff string (plus newline from print)."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "develop"
        diff_text = "compact diff content"
        mock_get_compact_diff.return_value = diff_text

        args = argparse.Namespace(project_dir=None, base_branch=None, exclude=None)
        execute_compact_diff(args)

        captured = capsys.readouterr()
        assert captured.out.strip() == diff_text


# ============================================================================
# Test Classes for Argument Handling
# ============================================================================


class TestCompactDiffArguments:
    """Test argument handling."""

    def test_exclude_passed_to_get_compact_diff(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test that args.exclude is forwarded to get_compact_diff."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = ""

        exclude_patterns = ["pr_info/**", "*.log"]
        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=exclude_patterns
        )
        execute_compact_diff(args)

        mock_get_compact_diff.assert_called_once_with(
            project_dir, "main", exclude_patterns
        )

    def test_base_branch_override(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test that args.base_branch skips detect_base_branch."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_get_compact_diff.return_value = ""

        args = argparse.Namespace(
            project_dir=None, base_branch="feature/base", exclude=None
        )
        result = execute_compact_diff(args)

        assert result == 0
        mock_detect_base_branch.assert_not_called()
        mock_get_compact_diff.assert_called_once_with(project_dir, "feature/base", [])

    def test_exclude_none_defaults_to_empty_list(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test that args.exclude=None is normalised to [] before passing."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = ""

        args = argparse.Namespace(project_dir=None, base_branch=None, exclude=None)
        execute_compact_diff(args)

        mock_get_compact_diff.assert_called_once_with(project_dir, "main", [])


# ============================================================================
# Test Classes for CLI Integration
# ============================================================================


class TestGitToolCommandIntegration:
    """Test CLI registration (no mocks — inspect parser)."""

    def test_git_tool_command_registered_in_cli(self) -> None:
        """Test that git-tool command is registered in CLI."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"
        subparser = subparsers_actions[0]
        assert "git-tool" in subparser.choices, "git-tool command should be registered"

    def test_compact_diff_subcommand_registered(self) -> None:
        """Test that compact-diff is registered as a subcommand of git-tool."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        subparsers = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        git_tool_parser = subparsers.choices["git-tool"]

        git_tool_subparsers = [
            action
            for action in git_tool_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert git_tool_subparsers, "git-tool should have subparsers"

        git_tool_subcommands = git_tool_subparsers[0]
        assert (
            "compact-diff" in git_tool_subcommands.choices
        ), "compact-diff should be a subcommand of git-tool"

    def test_exclude_flag_is_repeatable(self) -> None:
        """Test that --exclude can be specified multiple times (action=append)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        subparsers = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        git_tool_parser = subparsers.choices["git-tool"]

        git_tool_subparsers = [
            action
            for action in git_tool_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        compact_diff_parser = git_tool_subparsers.choices["compact-diff"]

        # Parse with multiple --exclude flags
        args = compact_diff_parser.parse_args(
            ["--exclude", "pattern1", "--exclude", "pattern2"]
        )
        assert args.exclude == ["pattern1", "pattern2"]
