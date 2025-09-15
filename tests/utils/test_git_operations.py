"""Tests for git operations functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from mcp_coder.utils.git_operations import (
    get_staged_changes,
    is_file_tracked,
    is_git_repository,
)


class TestGitDetection:
    """Test git repository and file tracking detection."""

    def test_is_git_repository_with_actual_repo(self, tmp_path: Path) -> None:
        """Test git repository detection using GitPython."""
        # Create actual git repo
        Repo.init(tmp_path)
        assert is_git_repository(tmp_path) is True

        # Non-git directory
        non_git = tmp_path / "subdir"
        non_git.mkdir()
        assert is_git_repository(non_git) is False

    def test_is_git_repository_with_invalid_repo(self, tmp_path: Path) -> None:
        """Test detection when .git exists but is invalid."""
        # Create a .git directory that's not a valid repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Should return False for invalid git repository
        assert is_git_repository(tmp_path) is False

    def test_is_file_tracked_without_git(self, tmp_path: Path) -> None:
        """Test file tracking when not in a git repository."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        assert is_file_tracked(test_file, tmp_path) is False

    def test_is_file_tracked_with_git(self, tmp_path: Path) -> None:
        """Test file tracking detection in git repository."""
        # Create git repo
        repo = Repo.init(tmp_path)

        # Create and add a file
        tracked_file = tmp_path / "tracked.txt"
        tracked_file.write_text("tracked content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")

        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked content")

        assert is_file_tracked(tracked_file, tmp_path) is True
        assert is_file_tracked(untracked_file, tmp_path) is False

    def test_is_file_tracked_outside_repo(self, tmp_path: Path) -> None:
        """Test file tracking for file outside repository."""
        # Create git repo in a subdirectory
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        Repo.init(repo_dir)

        # Create file outside the repo
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside content")

        # Should return False for file outside repo
        assert is_file_tracked(outside_file, repo_dir) is False

    def test_is_file_tracked_with_staged_file(self, tmp_path: Path) -> None:
        """Test detection of staged but uncommitted files."""
        # Create git repo
        repo = Repo.init(tmp_path)

        # Create and stage a file (but don't commit)
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged content")
        repo.index.add([str(staged_file)])

        # Staged files should be considered tracked
        assert is_file_tracked(staged_file, tmp_path) is True

    @patch("mcp_coder.utils.git_operations.Repo")
    def test_is_git_repository_with_exception(
        self, mock_repo: Mock, tmp_path: Path
    ) -> None:
        """Test handling of unexpected exceptions."""
        mock_repo.side_effect = Exception("Unexpected error")

        # Should return False and log warning
        assert is_git_repository(tmp_path) is False

    @patch("mcp_coder.utils.git_operations.Repo")
    def test_is_file_tracked_with_git_error(
        self, mock_repo: Mock, tmp_path: Path
    ) -> None:
        """Test handling of git command errors."""
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.git.ls_files.side_effect = GitCommandError("ls-files", 128)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Should return False on git errors
        assert is_file_tracked(test_file, tmp_path) is False


class TestGetStagedChanges:
    """Test get_staged_changes function."""

    def test_get_staged_changes_empty_repo(self, tmp_path: Path) -> None:
        """Test with empty repository - no staged files."""
        # Create git repo
        Repo.init(tmp_path)
        
        # Should return empty list
        result = get_staged_changes(tmp_path)
        assert result == []

    def test_get_staged_changes_clean_repo(self, tmp_path: Path) -> None:
        """Test with clean repository - files committed but none staged."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit a file
        test_file = tmp_path / "committed.txt"
        test_file.write_text("committed content")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")
        
        # Should return empty list - no staged changes
        result = get_staged_changes(tmp_path)
        assert result == []

    def test_get_staged_changes_with_staged_files(self, tmp_path: Path) -> None:
        """Test with some files staged for commit."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and stage multiple files
        file1 = tmp_path / "staged1.txt"
        file1.write_text("staged content 1")
        file2 = tmp_path / "subdir" / "staged2.txt"
        file2.parent.mkdir()
        file2.write_text("staged content 2")
        
        repo.index.add([str(file1), str(file2)])
        
        # Should return list of staged files
        result = get_staged_changes(tmp_path)
        assert "staged1.txt" in result
        assert "subdir/staged2.txt" in result or "subdir\\staged2.txt" in result
        assert len(result) == 2

    def test_get_staged_changes_mixed_staged_unstaged(self, tmp_path: Path) -> None:
        """Test with mix of staged and unstaged files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit initial file
        committed_file = tmp_path / "committed.txt"
        committed_file.write_text("committed content")
        repo.index.add([str(committed_file)])
        repo.index.commit("Initial commit")
        
        # Create staged file
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged content")
        repo.index.add([str(staged_file)])
        
        # Create unstaged file
        unstaged_file = tmp_path / "unstaged.txt"
        unstaged_file.write_text("unstaged content")
        
        # Modify committed file (will be unstaged)
        committed_file.write_text("modified content")
        
        # Should only return staged file
        result = get_staged_changes(tmp_path)
        assert "staged.txt" in result
        assert "unstaged.txt" not in result
        assert "committed.txt" not in result
        assert len(result) == 1

    def test_get_staged_changes_not_git_repo(self, tmp_path: Path) -> None:
        """Test with directory that is not a git repository."""
        # Create a regular directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should return empty list
        result = get_staged_changes(tmp_path)
        assert result == []

    def test_get_staged_changes_various_file_types(self, tmp_path: Path) -> None:
        """Test with various file types and paths."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files with different extensions and in subdirectories
        files_to_stage = [
            tmp_path / "script.py",
            tmp_path / "data.json",
            tmp_path / "docs" / "readme.md",
            tmp_path / "tests" / "test_example.py",
        ]
        
        for file_path in files_to_stage:
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(f"content for {file_path.name}")
            repo.index.add([str(file_path)])
        
        # Should return all staged files
        result = get_staged_changes(tmp_path)
        assert len(result) == 4
        assert "script.py" in result
        assert "data.json" in result
        # Check subdirectory files (handle both forward and back slashes)
        docs_found = any("docs" in path and "readme.md" in path for path in result)
        tests_found = any("tests" in path and "test_example.py" in path for path in result)
        assert docs_found
        assert tests_found

    @patch("mcp_coder.utils.git_operations.Repo")
    def test_get_staged_changes_git_command_error(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of git command failures."""
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.git.diff.side_effect = GitCommandError("diff", 128)
        
        # Should return empty list on git errors
        result = get_staged_changes(tmp_path)
        assert result == []

    @patch("mcp_coder.utils.git_operations.is_git_repository")
    def test_get_staged_changes_invalid_git_repo(self, mock_is_git: Mock, tmp_path: Path) -> None:
        """Test when git repository validation fails."""
        mock_is_git.return_value = False
        
        # Should return empty list when not a git repo
        result = get_staged_changes(tmp_path)
        assert result == []
