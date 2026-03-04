"""Tests for git-tool compact-diff uncommitted changes display.

This module tests the uncommitted changes display feature of the compact-diff
CLI command. Other compact-diff tests are in tests/cli/commands/test_git_tool.py.
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
        from mcp_coder.cli.commands.git_tool import (  # pylint: disable=no-name-in-module
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
