"""Tests for get_folder_git_status function."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.status import get_folder_git_status


class TestGetFolderGitStatus:
    """Tests for get_folder_git_status function."""

    def test_returns_missing_when_folder_not_exists(self, tmp_path: Path) -> None:
        """Returns 'Missing' when folder does not exist."""
        non_existent = tmp_path / "does_not_exist"

        result = get_folder_git_status(non_existent)

        assert result == "Missing"

    def test_returns_no_git_when_not_a_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'No Git' when folder exists but is not a git repo."""
        from mcp_coder.utils.subprocess_runner import CalledProcessError

        folder = tmp_path / "not_a_repo"
        folder.mkdir()

        def mock_execute(cmd: list[str], options: Any = None) -> None:
            # git rev-parse fails for non-git folders
            if "rev-parse" in cmd:
                raise CalledProcessError(128, cmd)
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(folder)

        assert result == "No Git"

    def test_returns_clean_when_no_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'Clean' when git repo has no uncommitted changes."""
        from mcp_coder.utils.subprocess_runner import CommandResult

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            # git rev-parse succeeds (is a git repo)
            if "rev-parse" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout=".git",
                    stderr="",
                    timed_out=False,
                )
            # git status --porcelain returns empty (clean)
            if "status" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout="",  # Empty = clean
                    stderr="",
                    timed_out=False,
                )
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(tmp_path)

        assert result == "Clean"

    def test_returns_dirty_when_has_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'Dirty' when git repo has uncommitted changes."""
        from mcp_coder.utils.subprocess_runner import CommandResult

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            # git rev-parse succeeds (is a git repo)
            if "rev-parse" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout=".git",
                    stderr="",
                    timed_out=False,
                )
            # git status --porcelain returns modified file
            if "status" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout="M file.py\n",  # Modified file
                    stderr="",
                    timed_out=False,
                )
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(tmp_path)

        assert result == "Dirty"

    def test_returns_error_when_git_status_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'Error' when git status command fails after rev-parse succeeds."""
        from mcp_coder.utils.subprocess_runner import CalledProcessError, CommandResult

        call_count = {"rev_parse": 0}

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            # git rev-parse succeeds (is a git repo)
            if "rev-parse" in cmd:
                call_count["rev_parse"] += 1
                return CommandResult(
                    return_code=0,
                    stdout=".git",
                    stderr="",
                    timed_out=False,
                )
            # git status fails
            if "status" in cmd:
                raise CalledProcessError(1, cmd)
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(tmp_path)

        assert result == "Error"
        assert call_count["rev_parse"] == 1  # Verify rev-parse was called
