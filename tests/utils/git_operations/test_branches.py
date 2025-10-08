"""Minimal tests for git branch operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    branch_exists,
    checkout_branch,
    create_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_parent_branch_name,
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
