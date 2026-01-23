"""Minimal tests for git branch mutation operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    branch_exists,
    checkout_branch,
    create_branch,
    get_current_branch_name,
)


@pytest.mark.git_integration
class TestBranchOperations:
    """Minimal tests for branch mutation operations - one test per function."""

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
