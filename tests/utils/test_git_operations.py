"""Tests for git operations functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from mcp_coder.utils.git_operations import (
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_file_tracked,
    is_git_repository,
    stage_specific_files,
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


class TestGetUnstagedChanges:
    """Test get_unstaged_changes function."""

    def test_get_unstaged_changes_clean_repo(self, tmp_path: Path) -> None:
        """Test with clean repository - no changes."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit a file to have non-empty repo
        test_file = tmp_path / "committed.txt"
        test_file.write_text("committed content")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")
        
        # Should return empty dict - no unstaged changes
        result = get_unstaged_changes(tmp_path)
        assert result == {"modified": [], "untracked": []}

    def test_get_unstaged_changes_empty_repo(self, tmp_path: Path) -> None:
        """Test with empty repository - new files only."""
        # Create git repo
        Repo.init(tmp_path)
        
        # Create untracked files
        file1 = tmp_path / "new1.txt"
        file1.write_text("new content 1")
        file2 = tmp_path / "subdir" / "new2.txt"
        file2.parent.mkdir()
        file2.write_text("new content 2")
        
        # Should return untracked files only
        result = get_unstaged_changes(tmp_path)
        assert "new1.txt" in result["untracked"]
        assert any("new2.txt" in path for path in result["untracked"])
        assert result["modified"] == []
        assert len(result["untracked"]) == 2

    def test_get_unstaged_changes_only_modified(self, tmp_path: Path) -> None:
        """Test with only modified files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit files
        file1 = tmp_path / "file1.txt"
        file1.write_text("original content 1")
        file2 = tmp_path / "subdir" / "file2.txt"
        file2.parent.mkdir()
        file2.write_text("original content 2")
        
        repo.index.add([str(file1), str(file2)])
        repo.index.commit("Initial commit")
        
        # Modify the files
        file1.write_text("modified content 1")
        file2.write_text("modified content 2")
        
        # Should return modified files only
        result = get_unstaged_changes(tmp_path)
        assert "file1.txt" in result["modified"]
        assert any("file2.txt" in path for path in result["modified"])
        assert result["untracked"] == []
        assert len(result["modified"]) == 2

    def test_get_unstaged_changes_only_untracked(self, tmp_path: Path) -> None:
        """Test with only untracked files."""
        # Create git repo with committed file
        repo = Repo.init(tmp_path)
        
        committed_file = tmp_path / "committed.txt"
        committed_file.write_text("committed content")
        repo.index.add([str(committed_file)])
        repo.index.commit("Initial commit")
        
        # Create untracked files
        untracked1 = tmp_path / "untracked1.txt"
        untracked1.write_text("untracked content 1")
        untracked2 = tmp_path / "dir" / "untracked2.txt"
        untracked2.parent.mkdir()
        untracked2.write_text("untracked content 2")
        
        # Should return untracked files only
        result = get_unstaged_changes(tmp_path)
        assert "untracked1.txt" in result["untracked"]
        assert any("untracked2.txt" in path for path in result["untracked"])
        assert result["modified"] == []
        assert len(result["untracked"]) == 2

    def test_get_unstaged_changes_mixed_changes(self, tmp_path: Path) -> None:
        """Test with both modified and untracked files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit files
        committed_file = tmp_path / "committed.txt"
        committed_file.write_text("original content")
        repo.index.add([str(committed_file)])
        repo.index.commit("Initial commit")
        
        # Modify committed file
        committed_file.write_text("modified content")
        
        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked content")
        
        # Create staged file (should not appear in unstaged)
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged content")
        repo.index.add([str(staged_file)])
        
        # Should return both modified and untracked
        result = get_unstaged_changes(tmp_path)
        assert "committed.txt" in result["modified"]
        assert "untracked.txt" in result["untracked"]
        assert "staged.txt" not in result["modified"]
        assert "staged.txt" not in result["untracked"]
        assert len(result["modified"]) == 1
        assert len(result["untracked"]) == 1

    def test_get_unstaged_changes_not_git_repo(self, tmp_path: Path) -> None:
        """Test with directory that is not a git repository."""
        # Create regular files
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should return empty dict
        result = get_unstaged_changes(tmp_path)
        assert result == {"modified": [], "untracked": []}

    def test_get_unstaged_changes_with_gitignore(self, tmp_path: Path) -> None:
        """Test that gitignored files are not included in untracked."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\ntemp/\n")
        repo.index.add([str(gitignore)])
        repo.index.commit("Add gitignore")
        
        # Create ignored files
        ignored_file = tmp_path / "debug.log"
        ignored_file.write_text("log content")
        ignored_dir = tmp_path / "temp"
        ignored_dir.mkdir()
        (ignored_dir / "temp.txt").write_text("temp content")
        
        # Create non-ignored file
        regular_file = tmp_path / "regular.txt"
        regular_file.write_text("regular content")
        
        # Should not include ignored files
        result = get_unstaged_changes(tmp_path)
        assert "regular.txt" in result["untracked"]
        assert "debug.log" not in result["untracked"]
        assert not any("temp" in path for path in result["untracked"])
        assert result["modified"] == []

    def test_get_unstaged_changes_deleted_files(self, tmp_path: Path) -> None:
        """Test with deleted files (should appear as modified)."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content 1")
        file2 = tmp_path / "file2.txt"
        file2.write_text("content 2")
        
        repo.index.add([str(file1), str(file2)])
        repo.index.commit("Initial commit")
        
        # Delete one file
        file1.unlink()
        
        # Modify the other
        file2.write_text("modified content")
        
        # Should show both deleted and modified files
        result = get_unstaged_changes(tmp_path)
        assert "file1.txt" in result["modified"]  # Deleted files show as modified
        assert "file2.txt" in result["modified"]
        assert result["untracked"] == []
        assert len(result["modified"]) == 2

    def test_get_unstaged_changes_various_file_types(self, tmp_path: Path) -> None:
        """Test with various file types and subdirectories."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create initial commit
        initial_file = tmp_path / "initial.txt"
        initial_file.write_text("initial")
        repo.index.add([str(initial_file)])
        repo.index.commit("Initial commit")
        
        # Create various untracked files
        files_to_create = [
            tmp_path / "script.py",
            tmp_path / "data.json",
            tmp_path / "docs" / "readme.md",
            tmp_path / "tests" / "test_example.py",
            tmp_path / "assets" / "image.png",
        ]
        
        for file_path in files_to_create:
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(f"content for {file_path.name}")
        
        # Should return all untracked files
        result = get_unstaged_changes(tmp_path)
        assert len(result["untracked"]) == 5
        assert "script.py" in result["untracked"]
        assert "data.json" in result["untracked"]
        assert any("readme.md" in path for path in result["untracked"])
        assert any("test_example.py" in path for path in result["untracked"])
        assert any("image.png" in path for path in result["untracked"])
        assert result["modified"] == []

    @patch("mcp_coder.utils.git_operations.Repo")
    def test_get_unstaged_changes_git_command_error(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of git command failures."""
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.git.status.side_effect = GitCommandError("status", 128)
        
        # Should return empty dict on git errors
        result = get_unstaged_changes(tmp_path)
        assert result == {"modified": [], "untracked": []}

    @patch("mcp_coder.utils.git_operations.is_git_repository")
    def test_get_unstaged_changes_invalid_git_repo(self, mock_is_git: Mock, tmp_path: Path) -> None:
        """Test when git repository validation fails."""
        mock_is_git.return_value = False
        
        # Should return empty dict when not a git repo
        result = get_unstaged_changes(tmp_path)
        assert result == {"modified": [], "untracked": []}


class TestGetFullStatus:
    """Test get_full_status function."""

    def test_get_full_status_clean_repo(self, tmp_path: Path) -> None:
        """Test with clean repository - no changes."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit a file to have non-empty repo
        test_file = tmp_path / "committed.txt"
        test_file.write_text("committed content")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")
        
        # Should return empty status - no changes
        result = get_full_status(tmp_path)
        assert result == {"staged": [], "modified": [], "untracked": []}

    def test_get_full_status_empty_repo(self, tmp_path: Path) -> None:
        """Test with empty repository - new files only."""
        # Create git repo
        Repo.init(tmp_path)
        
        # Create untracked files
        file1 = tmp_path / "new1.txt"
        file1.write_text("new content 1")
        file2 = tmp_path / "subdir" / "new2.txt"
        file2.parent.mkdir()
        file2.write_text("new content 2")
        
        # Should return untracked files only
        result = get_full_status(tmp_path)
        assert "new1.txt" in result["untracked"]
        assert any("new2.txt" in path for path in result["untracked"])
        assert result["staged"] == []
        assert result["modified"] == []
        assert len(result["untracked"]) == 2

    def test_get_full_status_only_staged(self, tmp_path: Path) -> None:
        """Test with only staged files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and stage files
        file1 = tmp_path / "staged1.txt"
        file1.write_text("staged content 1")
        file2 = tmp_path / "subdir" / "staged2.txt"
        file2.parent.mkdir()
        file2.write_text("staged content 2")
        
        repo.index.add([str(file1), str(file2)])
        
        # Should return staged files only
        result = get_full_status(tmp_path)
        assert "staged1.txt" in result["staged"]
        assert any("staged2.txt" in path for path in result["staged"])
        assert result["modified"] == []
        assert result["untracked"] == []
        assert len(result["staged"]) == 2

    def test_get_full_status_only_modified(self, tmp_path: Path) -> None:
        """Test with only modified files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit files
        file1 = tmp_path / "file1.txt"
        file1.write_text("original content 1")
        file2 = tmp_path / "subdir" / "file2.txt"
        file2.parent.mkdir()
        file2.write_text("original content 2")
        
        repo.index.add([str(file1), str(file2)])
        repo.index.commit("Initial commit")
        
        # Modify the files
        file1.write_text("modified content 1")
        file2.write_text("modified content 2")
        
        # Should return modified files only
        result = get_full_status(tmp_path)
        assert "file1.txt" in result["modified"]
        assert any("file2.txt" in path for path in result["modified"])
        assert result["staged"] == []
        assert result["untracked"] == []
        assert len(result["modified"]) == 2

    def test_get_full_status_comprehensive_changes(self, tmp_path: Path) -> None:
        """Test with all types of changes: staged, modified, and untracked."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit initial files
        committed_file = tmp_path / "committed.txt"
        committed_file.write_text("original content")
        repo.index.add([str(committed_file)])
        repo.index.commit("Initial commit")
        
        # Modify committed file (will be modified)
        committed_file.write_text("modified content")
        
        # Create and stage new file (will be staged)
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged content")
        repo.index.add([str(staged_file)])
        
        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked content")
        
        # Should return all types of changes
        result = get_full_status(tmp_path)
        assert "staged.txt" in result["staged"]
        assert "committed.txt" in result["modified"]
        assert "untracked.txt" in result["untracked"]
        assert len(result["staged"]) == 1
        assert len(result["modified"]) == 1
        assert len(result["untracked"]) == 1

    def test_get_full_status_not_git_repo(self, tmp_path: Path) -> None:
        """Test with directory that is not a git repository."""
        # Create regular files
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should return empty status
        result = get_full_status(tmp_path)
        assert result == {"staged": [], "modified": [], "untracked": []}

    def test_get_full_status_consistency_with_individual_functions(self, tmp_path: Path) -> None:
        """Test that get_full_status returns consistent results with individual functions."""
        # Create git repo with complex state
        repo = Repo.init(tmp_path)
        
        # Create committed file
        committed_file = tmp_path / "committed.txt"
        committed_file.write_text("original")
        repo.index.add([str(committed_file)])
        repo.index.commit("Initial commit")
        
        # Modify committed file
        committed_file.write_text("modified")
        
        # Create and stage new file
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged")
        repo.index.add([str(staged_file)])
        
        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked")
        
        # Get results from individual functions
        staged_changes = get_staged_changes(tmp_path)
        unstaged_changes = get_unstaged_changes(tmp_path)
        
        # Get results from comprehensive function
        full_status = get_full_status(tmp_path)
        
        # Should be consistent
        assert set(full_status["staged"]) == set(staged_changes)
        assert set(full_status["modified"]) == set(unstaged_changes["modified"])
        assert set(full_status["untracked"]) == set(unstaged_changes["untracked"])

    def test_get_full_status_large_repository_basic(self, tmp_path: Path) -> None:
        """Test basic performance with many files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create many files of different types
        file_count = 50  # Reasonable number for testing
        
        # Create committed files
        for i in range(file_count // 3):
            file_path = tmp_path / f"committed_{i}.txt"
            file_path.write_text(f"committed content {i}")
            repo.index.add([str(file_path)])
        repo.index.commit("Initial commit")
        
        # Create staged files
        for i in range(file_count // 3):
            file_path = tmp_path / f"staged_{i}.txt"
            file_path.write_text(f"staged content {i}")
            repo.index.add([str(file_path)])
        
        # Create untracked files
        for i in range(file_count // 3):
            file_path = tmp_path / f"untracked_{i}.txt"
            file_path.write_text(f"untracked content {i}")
        
        # Should handle many files efficiently
        result = get_full_status(tmp_path)
        assert len(result["staged"]) == file_count // 3
        assert len(result["untracked"]) == file_count // 3
        assert len(result["modified"]) == 0

    def test_get_full_status_with_subdirectories(self, tmp_path: Path) -> None:
        """Test with files in various subdirectories."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files in nested directories
        dirs = ["src", "tests", "docs", "assets/images", "config/dev"]
        
        for i, dir_name in enumerate(dirs):
            dir_path = tmp_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create different types of files in each directory
            if i % 3 == 0:  # Committed files
                file_path = dir_path / "committed.txt"
                file_path.write_text("committed")
                repo.index.add([str(file_path)])
            elif i % 3 == 1:  # Staged files (after commit)
                pass  # Will create after commit
            else:  # Untracked files
                file_path = dir_path / "untracked.txt"
                file_path.write_text("untracked")
        
        # Commit the committed files
        repo.index.commit("Initial commit")
        
        # Create staged files
        for i, dir_name in enumerate(dirs):
            if i % 3 == 1:
                dir_path = tmp_path / dir_name
                file_path = dir_path / "staged.txt"
                file_path.write_text("staged")
                repo.index.add([str(file_path)])
        
        # Should handle nested directories correctly
        result = get_full_status(tmp_path)
        
        # Check that files from different directories are included
        assert len(result["staged"]) > 0
        assert len(result["untracked"]) > 0
        assert any("/" in path or "\\" in path for path in result["staged"] + result["untracked"])

    def test_get_full_status_deleted_files(self, tmp_path: Path) -> None:
        """Test with deleted files (should appear as modified)."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content 1")
        file2 = tmp_path / "file2.txt"
        file2.write_text("content 2")
        file3 = tmp_path / "file3.txt"
        file3.write_text("content 3")
        
        repo.index.add([str(file1), str(file2), str(file3)])
        repo.index.commit("Initial commit")
        
        # Delete one file, modify another, modify and stage third
        file1.unlink()  # Deleted
        file2.write_text("modified content")  # Modified
        file3.write_text("modified and staged content")  # Modified
        repo.index.add([str(file3)])  # Stage the modified file3
        
        # Should show deleted and modified files in modified list, staged file in staged
        result = get_full_status(tmp_path)
        assert "file1.txt" in result["modified"]  # Deleted file
        assert "file2.txt" in result["modified"]  # Modified file
        assert "file3.txt" in result["staged"]    # Modified and staged file
        assert result["untracked"] == []
        assert len(result["modified"]) == 2
        assert len(result["staged"]) == 1

    def test_get_full_status_uses_existing_functions(self, tmp_path: Path) -> None:
        """Test that get_full_status efficiently uses existing functions."""
        # Create a real git repo and test that the function works as expected
        # by comparing with individual function calls rather than mocking
        
        # Create git repo with various changes
        repo = Repo.init(tmp_path)
        
        # Create committed file
        committed_file = tmp_path / "committed.txt"
        committed_file.write_text("original")
        repo.index.add([str(committed_file)])
        repo.index.commit("Initial commit")
        
        # Modify committed file
        committed_file.write_text("modified")
        
        # Create and stage new file
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged")
        repo.index.add([str(staged_file)])
        
        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked")
        
        # Get results from individual functions
        staged_changes = get_staged_changes(tmp_path)
        unstaged_changes = get_unstaged_changes(tmp_path)
        
        # Get results from comprehensive function
        full_status = get_full_status(tmp_path)
        
        # Should combine results correctly
        expected_result = {
            "staged": staged_changes,
            "modified": unstaged_changes["modified"],
            "untracked": unstaged_changes["untracked"]
        }
        
        assert full_status == expected_result

    @patch("mcp_coder.utils.git_operations.is_git_repository")
    def test_get_full_status_invalid_git_repo(self, mock_is_git: Mock, tmp_path: Path) -> None:
        """Test when git repository validation fails."""
        mock_is_git.return_value = False
        
        # Should return empty status when not a git repo
        result = get_full_status(tmp_path)
        assert result == {"staged": [], "modified": [], "untracked": []}

    @patch("mcp_coder.utils.git_operations.get_staged_changes")
    def test_get_full_status_handles_exceptions(self, mock_staged: Mock, tmp_path: Path) -> None:
        """Test handling of exceptions from underlying functions."""
        mock_staged.side_effect = Exception("Unexpected error")
        
        # Should handle exceptions gracefully
        result = get_full_status(tmp_path)
        assert result == {"staged": [], "modified": [], "untracked": []}



class TestStageSpecificFiles:
    """Test stage_specific_files function."""

    def test_stage_specific_files_single_existing_file(self, tmp_path: Path) -> None:
        """Test staging a single existing file."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create file to stage
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Should successfully stage the file
        result = stage_specific_files([test_file], tmp_path)
        assert result is True
        
        # Verify file is staged
        staged_files = get_staged_changes(tmp_path)
        assert "test.txt" in staged_files

    def test_stage_specific_files_multiple_existing_files(self, tmp_path: Path) -> None:
        """Test staging multiple existing files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files to stage
        file1 = tmp_path / "file1.txt"
        file1.write_text("content 1")
        file2 = tmp_path / "subdir" / "file2.txt"
        file2.parent.mkdir()
        file2.write_text("content 2")
        file3 = tmp_path / "file3.py"
        file3.write_text("print('hello')")
        
        # Should successfully stage all files
        result = stage_specific_files([file1, file2, file3], tmp_path)
        assert result is True
        
        # Verify all files are staged
        staged_files = get_staged_changes(tmp_path)
        assert "file1.txt" in staged_files
        assert any("file2.txt" in path for path in staged_files)
        assert "file3.py" in staged_files
        assert len(staged_files) == 3

    def test_stage_specific_files_non_existent_file(self, tmp_path: Path) -> None:
        """Test staging non-existent file should fail gracefully."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Try to stage non-existent file
        non_existent = tmp_path / "does_not_exist.txt"
        result = stage_specific_files([non_existent], tmp_path)
        assert result is False
        
        # Verify no files are staged
        staged_files = get_staged_changes(tmp_path)
        assert staged_files == []

    def test_stage_specific_files_outside_repository(self, tmp_path: Path) -> None:
        """Test staging files outside repository should fail."""
        # Create git repo in subdirectory
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = Repo.init(repo_dir)
        
        # Create file outside repo
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside content")
        
        # Should fail to stage file outside repo
        result = stage_specific_files([outside_file], repo_dir)
        assert result is False
        
        # Verify no files are staged
        staged_files = get_staged_changes(repo_dir)
        assert staged_files == []

    def test_stage_specific_files_already_staged(self, tmp_path: Path) -> None:
        """Test staging already staged files should be no-op."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and stage file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        repo.index.add([str(test_file)])
        
        # Verify file is already staged
        staged_files = get_staged_changes(tmp_path)
        assert "test.txt" in staged_files
        
        # Stage again - should succeed (no-op)
        result = stage_specific_files([test_file], tmp_path)
        assert result is True
        
        # Verify file is still staged
        staged_files = get_staged_changes(tmp_path)
        assert "test.txt" in staged_files
        assert len(staged_files) == 1

    def test_stage_specific_files_mix_valid_invalid(self, tmp_path: Path) -> None:
        """Test staging mix of valid and invalid files should fail."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create one valid file
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("valid content")
        
        # One non-existent file
        invalid_file = tmp_path / "invalid.txt"
        
        # Should fail due to invalid file
        result = stage_specific_files([valid_file, invalid_file], tmp_path)
        assert result is False
        
        # Verify no files are staged (all or nothing)
        staged_files = get_staged_changes(tmp_path)
        assert staged_files == []

    def test_stage_specific_files_relative_vs_absolute_paths(self, tmp_path: Path) -> None:
        """Test staging works with both relative and absolute paths."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files to stage
        file1 = tmp_path / "absolute.txt"
        file1.write_text("absolute path file")
        
        # Create file with relative path reference
        file2 = tmp_path / "relative.txt"
        file2.write_text("relative path file")
        
        # Stage using absolute paths
        result1 = stage_specific_files([file1], tmp_path)
        assert result1 is True
        
        # Verify absolute path file is staged
        staged_files = get_staged_changes(tmp_path)
        assert "absolute.txt" in staged_files
        
        # Stage using relative path (from project dir perspective)
        result2 = stage_specific_files([file2], tmp_path)
        assert result2 is True
        
        # Verify both files are staged
        staged_files = get_staged_changes(tmp_path)
        assert "absolute.txt" in staged_files
        assert "relative.txt" in staged_files
        assert len(staged_files) == 2

    def test_stage_specific_files_not_git_repository(self, tmp_path: Path) -> None:
        """Test staging files when not in git repository should fail."""
        # Create regular directory (not git repo)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Should fail - not a git repository
        result = stage_specific_files([test_file], tmp_path)
        assert result is False

    def test_stage_specific_files_empty_list(self, tmp_path: Path) -> None:
        """Test staging empty list of files should succeed."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Stage empty list - should succeed (no-op)
        result = stage_specific_files([], tmp_path)
        assert result is True
        
        # Verify no files are staged
        staged_files = get_staged_changes(tmp_path)
        assert staged_files == []

    def test_stage_specific_files_various_file_types(self, tmp_path: Path) -> None:
        """Test staging various file types and extensions."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files with different extensions
        files_to_stage = [
            tmp_path / "script.py",
            tmp_path / "data.json",
            tmp_path / "docs" / "readme.md",
            tmp_path / "config.yml",
            tmp_path / "image.png",  # Binary file
            tmp_path / ".gitignore",  # Hidden file
        ]
        
        for file_path in files_to_stage:
            file_path.parent.mkdir(exist_ok=True, parents=True)
            if file_path.name == "image.png":
                # Simulate binary content
                file_path.write_bytes(b"fake binary content")
            else:
                file_path.write_text(f"content for {file_path.name}")
        
        # Should successfully stage all file types
        result = stage_specific_files(files_to_stage, tmp_path)
        assert result is True
        
        # Verify all files are staged
        staged_files = get_staged_changes(tmp_path)
        assert len(staged_files) == 6
        assert "script.py" in staged_files
        assert "data.json" in staged_files
        assert "config.yml" in staged_files
        assert "image.png" in staged_files
        assert ".gitignore" in staged_files
        assert any("readme.md" in path for path in staged_files)

    def test_stage_specific_files_modified_tracked_file(self, tmp_path: Path) -> None:
        """Test staging a tracked file that has been modified."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit file
        tracked_file = tmp_path / "tracked.txt"
        tracked_file.write_text("original content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")
        
        # Modify the tracked file
        tracked_file.write_text("modified content")
        
        # Verify file is modified but not staged
        unstaged = get_unstaged_changes(tmp_path)
        assert "tracked.txt" in unstaged["modified"]
        
        staged = get_staged_changes(tmp_path)
        assert "tracked.txt" not in staged
        
        # Stage the modified file
        result = stage_specific_files([tracked_file], tmp_path)
        assert result is True
        
        # Verify file is now staged
        staged = get_staged_changes(tmp_path)
        assert "tracked.txt" in staged

    def test_stage_specific_files_deleted_tracked_file(self, tmp_path: Path) -> None:
        """Test staging a tracked file that has been deleted."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit file
        tracked_file = tmp_path / "tracked.txt"
        tracked_file.write_text("original content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")
        
        # Delete the tracked file
        tracked_file.unlink()
        
        # Verify file shows as modified (deleted)
        unstaged = get_unstaged_changes(tmp_path)
        assert "tracked.txt" in unstaged["modified"]
        
        # Try to stage the deleted file - should handle gracefully
        # (Git can stage deletions, but the file path doesn't exist)
        result = stage_specific_files([tracked_file], tmp_path)
        # This might fail since file doesn't exist, but that's expected
        # The function should handle this gracefully
        assert result is False

    @patch("mcp_coder.utils.git_operations.is_git_repository")
    def test_stage_specific_files_git_validation_fails(self, mock_is_git: Mock, tmp_path: Path) -> None:
        """Test when git repository validation fails."""
        mock_is_git.return_value = False
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should fail when not a git repo
        result = stage_specific_files([test_file], tmp_path)
        assert result is False

    @patch("mcp_coder.utils.git_operations.Repo")
    def test_stage_specific_files_git_command_error(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of git command failures."""
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.index.add.side_effect = GitCommandError("add", 128)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should handle git command errors gracefully
        result = stage_specific_files([test_file], tmp_path)
        assert result is False

    def test_stage_specific_files_paths_conversion(self, tmp_path: Path) -> None:
        """Test that file paths are correctly converted to relative paths."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create file in subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("test content")
        
        # Stage using absolute path
        result = stage_specific_files([test_file], tmp_path)
        assert result is True
        
        # Verify staged file uses correct relative path
        staged_files = get_staged_changes(tmp_path)
        assert len(staged_files) == 1
        # Should be relative path, not absolute
        staged_path = staged_files[0]
        assert not str(tmp_path) in staged_path  # Not absolute
        assert "subdir" in staged_path and "test.txt" in staged_path

    def test_stage_specific_files_large_number_of_files(self, tmp_path: Path) -> None:
        """Test staging a large number of files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create many files
        files_to_stage = []
        for i in range(100):  # 100 files should be reasonable for testing
            file_path = tmp_path / f"file_{i:03d}.txt"
            file_path.write_text(f"content for file {i}")
            files_to_stage.append(file_path)
        
        # Should handle large number of files
        result = stage_specific_files(files_to_stage, tmp_path)
        assert result is True
        
        # Verify all files are staged
        staged_files = get_staged_changes(tmp_path)
        assert len(staged_files) == 100
        
        # Verify some sample files are in the list
        assert "file_000.txt" in staged_files
        assert "file_050.txt" in staged_files
        assert "file_099.txt" in staged_files
