"""Tests for get_folder_git_status function."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.vscodeclaude.status import (
    check_folder_dirty,
    get_folder_git_status,
)

_MODULE = "mcp_coder.workflows.vscodeclaude.status"


def _status(success: bool, clean: bool) -> dict[str, Any]:
    """Build a fake get_working_tree_status result."""
    return {
        "success": success,
        "error": None if success else "git status failed (exit 128)",
        "returncode": 0 if success else 128,
        "stderr": "",
        "clean": clean,
        "staged": [],
        "modified": [] if clean else ["file.py"],
        "untracked": [],
    }


class TestGetFolderGitStatus:
    """Tests for get_folder_git_status function."""

    def test_returns_missing_when_folder_not_exists(self, tmp_path: Path) -> None:
        """Returns 'Missing' when folder does not exist; git is never queried."""
        non_existent = tmp_path / "does_not_exist"

        with (
            patch(f"{_MODULE}.is_git_repository") as mock_is_repo,
            patch(f"{_MODULE}.get_working_tree_status") as mock_status,
        ):
            result = get_folder_git_status(non_existent)

        assert result == "Missing"
        mock_is_repo.assert_not_called()
        mock_status.assert_not_called()

    def test_returns_no_git_when_not_a_repo(self, tmp_path: Path) -> None:
        """Returns 'No Git' when folder exists but is not a git repo."""
        with (
            patch(f"{_MODULE}.is_git_repository", return_value=False),
            patch(f"{_MODULE}.get_working_tree_status") as mock_status,
        ):
            result = get_folder_git_status(tmp_path)

        assert result == "No Git"
        mock_status.assert_not_called()

    def test_returns_clean_when_no_changes(self, tmp_path: Path) -> None:
        """Returns 'Clean' when git repo has no uncommitted changes."""
        with (
            patch(f"{_MODULE}.is_git_repository", return_value=True),
            patch(
                f"{_MODULE}.get_working_tree_status",
                return_value=_status(success=True, clean=True),
            ) as mock_status,
        ):
            result = get_folder_git_status(tmp_path)

        assert result == "Clean"
        mock_status.assert_called_once_with(tmp_path)

    def test_returns_dirty_when_has_changes(self, tmp_path: Path) -> None:
        """Returns 'Dirty' when git repo has uncommitted changes."""
        with (
            patch(f"{_MODULE}.is_git_repository", return_value=True),
            patch(
                f"{_MODULE}.get_working_tree_status",
                return_value=_status(success=True, clean=False),
            ),
        ):
            result = get_folder_git_status(tmp_path)

        assert result == "Dirty"

    def test_returns_error_when_git_status_fails(self, tmp_path: Path) -> None:
        """Returns 'Error' (never 'Clean') when git status fails."""
        mock_is_repo = MagicMock(return_value=True)
        with (
            patch(f"{_MODULE}.is_git_repository", mock_is_repo),
            patch(
                f"{_MODULE}.get_working_tree_status",
                return_value=_status(success=False, clean=False),
            ),
        ):
            result = get_folder_git_status(tmp_path)
            dirty = check_folder_dirty(tmp_path)

        assert result == "Error"
        assert dirty is True  # cleanup never deletes on a git failure
        mock_is_repo.assert_called_with(tmp_path)
