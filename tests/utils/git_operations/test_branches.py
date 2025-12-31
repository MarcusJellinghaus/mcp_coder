"""Minimal tests for git branch operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    branch_exists,
    checkout_branch,
    create_branch,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_parent_branch_name,
    remote_branch_exists,
    validate_branch_name,
)


@pytest.mark.git_integration
class TestBranchOperations:
    """Minimal tests for branch operations - one test per function."""

    def test_create_and_branch_exists(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test create_branch and branch_exists work together."""
        _repo, project_dir = git_repo_with_commit

        # Create new branch (also checks it out)
        assert create_branch("feature-branch", project_dir) is True

        # Verify it exists
        assert branch_exists(project_dir, "feature-branch") is True
        assert branch_exists(project_dir, "nonexistent-branch") is False

    def test_checkout_branch_and_get_current(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test checkout_branch and get_current_branch_name work together."""
        _repo, project_dir = git_repo_with_commit

        # Create new branch (also checks it out)
        create_branch("feature-branch", project_dir)

        # Verify current branch (create_branch already checked it out)
        assert get_current_branch_name(project_dir) == "feature-branch"

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
        _repo, project_dir = git_repo_with_commit

        # Get initial branch name
        initial_branch = get_current_branch_name(project_dir)

        # Create feature branch (also checks it out)
        create_branch("feature-branch", project_dir)

        # Parent should be the initial branch
        parent = get_parent_branch_name(project_dir)
        assert parent == initial_branch

    def test_checkout_branch_from_remote(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test checkout_branch can create local branch from remote."""
        repo, project_dir = git_repo_with_commit

        # Get initial branch
        initial_branch = get_current_branch_name(project_dir)
        assert initial_branch is not None

        # Create a test branch and commit
        create_branch("remote-test-branch", project_dir)
        (project_dir / "test_file.txt").write_text("test content")
        repo.index.add(["test_file.txt"])
        repo.index.commit("Test commit on remote-test-branch")

        # Push to remote (use bare repo as remote)
        # First ensure we have a remote (git_repo_with_commit should have one)
        if "origin" not in [remote.name for remote in repo.remotes]:
            pytest.skip("No origin remote configured")

        # Push the branch to remote
        repo.git.push("-u", "origin", "remote-test-branch")

        # Go back to initial branch and delete local copy
        checkout_branch(initial_branch, project_dir)
        repo.git.branch("-D", "remote-test-branch")

        # Verify branch doesn't exist locally
        assert branch_exists(project_dir, "remote-test-branch") is False

        # Checkout from remote - should create local tracking branch
        assert checkout_branch("remote-test-branch", project_dir) is True

        # Verify we're on the branch and it exists locally
        assert get_current_branch_name(project_dir) == "remote-test-branch"
        assert branch_exists(project_dir, "remote-test-branch") is True


class TestValidateBranchName:
    """Tests for validate_branch_name function."""

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


class TestExtractIssueNumberFromBranch:
    """Tests for extract_issue_number_from_branch utility function."""

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
class TestRemoteBranchExists:
    """Tests for remote_branch_exists function."""

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
