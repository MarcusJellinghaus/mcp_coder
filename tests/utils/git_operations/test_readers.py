"""Tests for git repository reader operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    get_parent_branch_name,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
    remote_branch_exists,
    validate_branch_name,
)


@pytest.mark.git_integration
class TestRepositoryReaders:
    """Tests for repository status reader functions."""

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

    def test_is_working_directory_clean_ignore_files_none(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files=None preserves existing behavior."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file
        new_file = project_dir / "new.txt"
        new_file.write_text("new content")

        # Should return False - untracked file detected
        assert is_working_directory_clean(project_dir, ignore_files=None) is False

    def test_is_working_directory_clean_ignore_files_empty_list(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files=[] behaves same as None (backward compatibility)."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file
        new_file = project_dir / "new.txt"
        new_file.write_text("new content")

        # Should return False - empty list should not filter anything
        assert is_working_directory_clean(project_dir, ignore_files=[]) is False

    def test_is_working_directory_clean_ignore_files_matches_untracked(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files filters matching untracked file."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file that should be ignored
        uv_lock = project_dir / "uv.lock"
        uv_lock.write_text("lock content")

        # Should return True - uv.lock is ignored, directory is clean
        assert is_working_directory_clean(project_dir, ignore_files=["uv.lock"]) is True

    def test_is_working_directory_clean_ignore_files_other_untracked(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files does not filter non-matching files."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file that does NOT match ignore_files
        other_file = project_dir / "other.txt"
        other_file.write_text("other content")

        # Should return False - other.txt is not ignored
        assert (
            is_working_directory_clean(project_dir, ignore_files=["uv.lock"]) is False
        )

    def test_is_working_directory_clean_ignore_files_with_other_changes(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files with matching file AND other changes."""
        _repo, project_dir = git_repo_with_commit

        # Create ignored file AND another untracked file
        uv_lock = project_dir / "uv.lock"
        uv_lock.write_text("lock content")

        real_change = project_dir / "real_change.txt"
        real_change.write_text("real change content")

        # Should return False - real_change.txt is still detected
        assert (
            is_working_directory_clean(project_dir, ignore_files=["uv.lock"]) is False
        )


class TestBranchValidation:
    """Tests for branch name validation."""

    def test_valid_names(self) -> None:
        """Test valid branch names return True."""
        assert validate_branch_name("main") is True
        assert validate_branch_name("feature/xyz") is True
        assert validate_branch_name("123-fix-bug") is True

    def test_invalid_empty(self) -> None:
        """Test empty branch names return False."""
        assert validate_branch_name("") is False
        assert validate_branch_name("   ") is False  # whitespace-only

    def test_invalid_characters(self) -> None:
        """Test branch names with invalid characters return False."""
        # Test one representative invalid character
        assert validate_branch_name("branch~1") is False
        assert validate_branch_name("feature^branch") is False
        assert validate_branch_name("fix:bug") is False
        assert validate_branch_name("branch?name") is False
        assert validate_branch_name("feature*branch") is False
        assert validate_branch_name("branch[name]") is False


class TestBranchNameExtraction:
    """Tests for extracting issue numbers from branch names."""

    def test_extract_issue_number_from_branch_valid(self) -> None:
        """Tests extraction from valid branch names."""
        assert extract_issue_number_from_branch("123-feature-name") == 123
        assert extract_issue_number_from_branch("1-fix") == 1
        assert extract_issue_number_from_branch("999-long-branch-name-here") == 999

    def test_extract_issue_number_from_branch_invalid(self) -> None:
        """Tests extraction from invalid branch names returns None."""
        assert extract_issue_number_from_branch("feature-branch") is None
        assert extract_issue_number_from_branch("main") is None
        assert (
            extract_issue_number_from_branch("feature-123-name") is None
        )  # Number not at start

    def test_extract_issue_number_from_branch_edge_cases(self) -> None:
        """Tests edge cases for issue number extraction."""
        assert extract_issue_number_from_branch("") is None
        assert extract_issue_number_from_branch("123") is None  # No hyphen after number
        assert (
            extract_issue_number_from_branch("-feature") is None
        )  # No number before hyphen


@pytest.mark.git_integration
class TestBranchExistence:
    """Tests for branch existence checks."""

    def test_branch_exists(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test branch_exists detects local branches."""
        repo, project_dir = git_repo_with_commit

        # Get current branch name
        current_branch = repo.active_branch.name

        # Current branch should exist
        assert branch_exists(project_dir, current_branch) is True

        # Non-existent branch should not exist
        assert branch_exists(project_dir, "nonexistent-branch") is False

    def test_remote_branch_exists_returns_true(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test remote_branch_exists returns True for existing remote branch."""
        repo, project_dir, _ = git_repo_with_remote
        # Get actual branch name (could be master or main depending on git config)
        current_branch = repo.active_branch.name
        # Push current branch to remote
        repo.git.push("-u", "origin", current_branch)
        assert remote_branch_exists(project_dir, current_branch) is True

    def test_remote_branch_exists_returns_false_for_nonexistent(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test remote_branch_exists returns False for non-existing remote branch."""
        _, project_dir, _ = git_repo_with_remote
        assert remote_branch_exists(project_dir, "nonexistent-branch") is False

    def test_remote_branch_exists_returns_false_no_origin(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test remote_branch_exists returns False when no origin remote."""
        _, project_dir = git_repo_with_commit
        assert remote_branch_exists(project_dir, "master") is False

    def test_remote_branch_exists_invalid_inputs(self, tmp_path: Path) -> None:
        """Test remote_branch_exists returns False for invalid inputs."""
        assert remote_branch_exists(tmp_path, "master") is False  # Not a repo

    def test_remote_branch_exists_empty_branch_name(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test remote_branch_exists returns False for empty branch name."""
        _, project_dir, _ = git_repo_with_remote
        assert remote_branch_exists(project_dir, "") is False


@pytest.mark.git_integration
class TestBranchNameReaders:
    """Tests for branch name reader functions."""

    def test_get_current_branch_name(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_current_branch_name returns current branch."""
        repo, project_dir = git_repo_with_commit

        # Get actual branch name
        expected_branch = repo.active_branch.name

        # Should return the current branch
        assert get_current_branch_name(project_dir) == expected_branch

    def test_get_default_branch_name(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_default_branch_name returns main or master."""
        _repo, project_dir = git_repo_with_commit

        default_branch = get_default_branch_name(project_dir)
        assert default_branch in ["main", "master"]

    def test_get_parent_branch_name(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_parent_branch_name returns parent branch."""
        repo, project_dir = git_repo_with_commit

        # Get initial branch name
        initial_branch = get_current_branch_name(project_dir)

        # Create feature branch
        repo.git.checkout("-b", "feature-branch")

        # Parent should be the initial branch
        parent = get_parent_branch_name(project_dir)
        assert parent == initial_branch
