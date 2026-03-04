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

        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=None, committed_only=False
        )
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

        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=None, committed_only=False
        )
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
            project_dir="/not/a/repo",
            base_branch=None,
            exclude=None,
            committed_only=False,
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

        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=None, committed_only=False
        )
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

        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=None, committed_only=False
        )
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

        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=None, committed_only=False
        )
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
            project_dir=None,
            base_branch=None,
            exclude=exclude_patterns,
            committed_only=False,
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
            project_dir=None,
            base_branch="feature/base",
            exclude=None,
            committed_only=False,
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

        args = argparse.Namespace(
            project_dir=None, base_branch=None, exclude=None, committed_only=False
        )
        execute_compact_diff(args)

        mock_get_compact_diff.assert_called_once_with(project_dir, "main", [])


# ============================================================================
# Test Classes for Committed Only Flag
# ============================================================================


class TestCompactDiffCommittedOnlyFlag:
    """Test --committed-only flag parsing."""

    def test_committed_only_flag_absent_defaults_to_false(self) -> None:
        """Test that args.committed_only defaults to False when flag is absent."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["git-tool", "compact-diff"])

        assert args.committed_only is False

    def test_committed_only_flag_present_sets_to_true(self) -> None:
        """Test that args.committed_only is True when --committed-only flag is used."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["git-tool", "compact-diff", "--committed-only"])

        assert args.committed_only is True

    def test_committed_only_flag_with_other_arguments(self) -> None:
        """Test that --committed-only works alongside --exclude and --base-branch."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "git-tool",
                "compact-diff",
                "--committed-only",
                "--base-branch",
                "main",
                "--exclude",
                "*.log",
            ]
        )

        assert args.committed_only is True
        assert args.base_branch == "main"
        assert args.exclude == ["*.log"]


# ============================================================================
# Test Classes for Uncommitted Changes Display
# ============================================================================


class TestCompactDiffUncommittedChanges:
    """Test uncommitted changes display in compact-diff output."""

    def test_shows_uncommitted_changes_by_default(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that uncommitted changes are shown by default (without --committed-only)."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\ndiff --git bar.py\n+staged change"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=None,
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "diff --git foo.py" in captured.out
            assert "=== UNCOMMITTED CHANGES ===" in captured.out
            assert "=== STAGED CHANGES ===" in captured.out
            assert "staged change" in captured.out

    def test_committed_only_flag_suppresses_uncommitted(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that --committed-only flag suppresses uncommitted changes."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = "=== STAGED CHANGES ===\ndiff --git bar.py"

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=None,
                committed_only=True,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "diff --git foo.py" in captured.out
            assert "UNCOMMITTED CHANGES" not in captured.out
            mock_uncommitted.assert_not_called()

    def test_clean_working_directory_skips_uncommitted_section(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that uncommitted section is skipped when working directory is clean."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = ""

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=None,
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "diff --git foo.py" in captured.out
            assert "UNCOMMITTED CHANGES" not in captured.out

    def test_no_committed_changes_only_uncommitted(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test 'No committed changes' message when only uncommitted changes exist."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = ""

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\ndiff --git bar.py\n+staged change"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=None,
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "No committed changes" in captured.out
            assert "=== UNCOMMITTED CHANGES ===" in captured.out
            assert "staged change" in captured.out

    def test_git_diff_error_none_skips_uncommitted_section(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that None return from get_git_diff_for_commit (git error) skips uncommitted section."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = None

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=None,
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "diff --git foo.py" in captured.out
            assert "UNCOMMITTED CHANGES" not in captured.out

    def test_both_committed_and_uncommitted_present(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test output format when both committed and uncommitted changes exist."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git committed.py\n+committed"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\n"
                "diff --git staged.py\n"
                "+staged\n"
                "\n"
                "=== UNSTAGED CHANGES ===\n"
                "diff --git modified.py\n"
                "+modified\n"
                "\n"
                "=== UNTRACKED FILES ===\n"
                "diff --git new.py\n"
                "+new file"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=None,
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            output = captured.out
            committed_idx = output.find("diff --git committed.py")
            uncommitted_header_idx = output.find("=== UNCOMMITTED CHANGES ===")
            staged_header_idx = output.find("=== STAGED CHANGES ===")

            assert committed_idx < uncommitted_header_idx
            assert uncommitted_header_idx < staged_header_idx

            assert "=== STAGED CHANGES ===" in output
            assert "=== UNSTAGED CHANGES ===" in output
            assert "=== UNTRACKED FILES ===" in output

    def test_exclude_patterns_apply_to_uncommitted_changes(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that --exclude patterns filter uncommitted changes."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git committed.py\n+committed"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\n"
                "diff --git staged.py staged.py\n"
                "+staged python\n"
                "diff --git debug.log debug.log\n"
                "+log file content"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=["*.log"],
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "staged.py" in captured.out
            assert "staged python" in captured.out
            assert "debug.log" not in captured.out
            assert "log file content" not in captured.out

    def test_multiple_exclude_patterns_on_uncommitted(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that multiple --exclude patterns filter uncommitted changes."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = ""

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\n"
                "diff --git code.py code.py\n"
                "+python code\n"
                "diff --git test.log test.log\n"
                "+log content\n"
                "diff --git data.json data.json\n"
                "+json data"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=["*.log", "*.json"],
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "code.py" in captured.out
            assert "python code" in captured.out
            assert "test.log" not in captured.out
            assert "data.json" not in captured.out

    def test_exclude_all_uncommitted_changes(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that excluding all uncommitted files results in no uncommitted section."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = "diff --git committed.py\n+committed"

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\n"
                "diff --git debug.log debug.log\n"
                "+log content"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=["*.log"],
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "UNCOMMITTED CHANGES" not in captured.out
            assert "debug.log" not in captured.out

    def test_exclude_path_prefix_on_uncommitted(
        self,
        mock_get_compact_diff: MagicMock,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that path prefix patterns (e.g., pr_info/**) filter uncommitted changes."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"
        mock_get_compact_diff.return_value = ""

        with patch(
            "mcp_coder.cli.commands.git_tool.get_git_diff_for_commit"
        ) as mock_uncommitted:
            mock_uncommitted.return_value = (
                "=== STAGED CHANGES ===\n"
                "diff --git src/main.py src/main.py\n"
                "+source code\n"
                "diff --git pr_info/notes.md pr_info/notes.md\n"
                "+notes content"
            )

            args = argparse.Namespace(
                project_dir=None,
                base_branch=None,
                exclude=["pr_info/**"],
                committed_only=False,
            )
            result = execute_compact_diff(args)

            assert result == 0
            captured = capsys.readouterr()

            assert "src/main.py" in captured.out
            assert "source code" in captured.out
            assert "pr_info/notes.md" not in captured.out
            assert "notes content" not in captured.out

    def test_apply_exclude_patterns_to_uncommitted_diff_helper(self) -> None:
        """Test the helper function that filters uncommitted diff by exclude patterns."""
        from mcp_coder.cli.commands.git_tool import (
            _apply_exclude_patterns_to_uncommitted_diff,
        )

        uncommitted_diff = (
            "=== STAGED CHANGES ===\n"
            "diff --git code.py code.py\n"
            "+python\n"
            "diff --git test.log test.log\n"
            "+log\n"
            "\n"
            "=== UNSTAGED CHANGES ===\n"
            "diff --git data.json data.json\n"
            "+json"
        )

        filtered = _apply_exclude_patterns_to_uncommitted_diff(
            uncommitted_diff, ["*.log"]
        )

        assert "code.py" in filtered
        assert "test.log" not in filtered
        assert "data.json" in filtered


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
