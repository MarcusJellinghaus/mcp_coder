"""Tests for workflow utility functions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.workflows.utils import resolve_project_dir


class TestResolveProjectDir:
    """Test resolve_project_dir function."""

    def test_resolve_project_dir_none_uses_cwd(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with None uses current working directory."""
        # Create .git directory in temp path
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = resolve_project_dir(None)
            assert result == tmp_path

    def test_resolve_project_dir_with_valid_path(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with valid project directory."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = resolve_project_dir(str(tmp_path))
        assert result == tmp_path

    def test_resolve_project_dir_invalid_path_raises_value_error(self) -> None:
        """Test resolve_project_dir with invalid path raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            resolve_project_dir("/invalid/nonexistent/path")

    def test_resolve_project_dir_not_directory_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir with non-directory path raises ValueError."""
        # Create a file instead of directory
        test_file = tmp_path / "test_file"
        test_file.write_text("test content")

        with pytest.raises(ValueError, match="not a directory"):
            resolve_project_dir(str(test_file))

    def test_resolve_project_dir_no_git_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir without .git directory raises ValueError."""
        with pytest.raises(ValueError, match="not a git repository"):
            resolve_project_dir(str(tmp_path))

    def test_resolve_project_dir_permission_error_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir with permission error raises ValueError."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock permission error during directory listing
        with patch.object(
            Path, "iterdir", side_effect=PermissionError("Access denied")
        ):
            with pytest.raises(ValueError, match="No read access"):
                resolve_project_dir(str(tmp_path))

    def test_resolve_project_dir_resolve_error_raises_value_error(self) -> None:
        """Test resolve_project_dir with path resolve error raises ValueError."""
        # Mock OSError during path resolution
        with patch.object(Path, "resolve", side_effect=OSError("Path error")):
            with pytest.raises(ValueError, match="Invalid project directory path"):
                resolve_project_dir("/some/path")
