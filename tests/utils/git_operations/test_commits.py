"""Minimal tests for git commit operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import commit_all_changes, commit_staged_files


@pytest.mark.git_integration
class TestCommitOperations:
    """Minimal tests for commit operations - one test per function."""

    def test_commit_staged_files(self, git_repo: tuple[Repo, Path]) -> None:
        """Test commit_staged_files commits staged changes."""
        repo, project_dir = git_repo

        # Create and stage a file
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        repo.index.add(["test.py"])

        # Commit staged files
        result = commit_staged_files("Add test file", project_dir)

        assert result["success"] is True
        assert result["error"] is None
        assert len(list(repo.iter_commits())) == 1

    def test_commit_all_changes(self, git_repo: tuple[Repo, Path]) -> None:
        """Test commit_all_changes stages and commits in one operation."""
        repo, project_dir = git_repo

        # Create a file (not staged)
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")

        # Commit all changes (should stage + commit)
        result = commit_all_changes("Add test file", project_dir)

        assert result["success"] is True
        assert result["error"] is None
        assert len(list(repo.iter_commits())) == 1

    def test_commit_with_multiline_message(self, git_repo: tuple[Repo, Path]) -> None:
        """Test commit handles multiline commit messages."""
        repo, project_dir = git_repo

        # Create file
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")

        # Commit with multiline message
        multiline_message = (
            "Add test file\n\nThis is a detailed description\nwith multiple lines"
        )
        result = commit_all_changes(multiline_message, project_dir)

        assert result["success"] is True
        commits = list(repo.iter_commits())
        assert commits[0].message.strip() == multiline_message
