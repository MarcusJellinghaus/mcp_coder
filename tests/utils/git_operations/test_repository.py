"""Minimal tests for git repository operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
)


@pytest.mark.git_integration
class TestRepositoryOperations:
    """Minimal tests for repository operations - one test per function."""

    def test_is_git_repository(
        self, git_repo: tuple[Repo, Path], tmp_path: Path
    ) -> None:
        """Test is_git_repository detects git repos."""
        _repo, project_dir = git_repo

        # Should detect git repo
        assert is_git_repository(project_dir) is True

        # Should not detect non-git directory
        non_git_dir = tmp_path / "not_a_repo"
        non_git_dir.mkdir()
        assert is_git_repository(non_git_dir) is False

    def test_is_working_directory_clean(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test is_working_directory_clean detects changes."""
        _repo, project_dir = git_repo_with_commit

        # Clean working directory
        assert is_working_directory_clean(project_dir) is True

        # Add untracked file
        new_file = project_dir / "new.py"
        new_file.write_text("# New file")
        assert is_working_directory_clean(project_dir) is False

    def test_get_staged_changes(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test get_staged_changes returns staged files."""
        repo, project_dir = git_repo_with_commit

        # No staged changes initially
        staged = get_staged_changes(project_dir)
        assert staged == []

        # Stage a file
        new_file = project_dir / "staged.py"
        new_file.write_text("# Staged file")
        repo.index.add(["staged.py"])

        # Should detect staged file
        staged = get_staged_changes(project_dir)
        assert len(staged) == 1
        assert "staged.py" in staged[0]

    def test_get_unstaged_changes(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_unstaged_changes returns modified files."""
        _repo, project_dir = git_repo_with_commit

        # No unstaged changes initially
        unstaged = get_unstaged_changes(project_dir)
        assert unstaged == {"modified": [], "untracked": []}

        # Modify tracked file
        readme = project_dir / "README.md"
        readme.write_text("# Modified")

        # Should detect unstaged change
        unstaged = get_unstaged_changes(project_dir)
        assert len(unstaged["modified"]) == 1
        assert "README.md" in unstaged["modified"][0]

    def test_get_full_status(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test get_full_status returns complete status."""
        repo, project_dir = git_repo_with_commit

        # Create staged, modified, and untracked files
        staged_file = project_dir / "staged.py"
        staged_file.write_text("# Staged")
        repo.index.add(["staged.py"])

        modified_file = project_dir / "README.md"
        modified_file.write_text("# Modified")

        untracked_file = project_dir / "untracked.py"
        untracked_file.write_text("# Untracked")

        # Get full status
        status = get_full_status(project_dir)

        assert "staged" in status
        assert "modified" in status
        assert "untracked" in status
        assert any("staged.py" in f for f in status["staged"])
        assert any("README.md" in f for f in status["modified"])
        assert any("untracked.py" in f for f in status["untracked"])
