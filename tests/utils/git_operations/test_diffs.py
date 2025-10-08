"""Minimal tests for git diff operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    checkout_branch,
    commit_all_changes,
    create_branch,
    get_branch_diff,
    get_current_branch_name,
    get_git_diff_for_commit,
)


@pytest.mark.git_integration
class TestDiffOperations:
    """Minimal tests for diff operations - one test per function."""

    def test_get_git_diff_for_commit(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_git_diff_for_commit returns diff for staged/unstaged changes."""
        _repo, project_dir = git_repo_with_commit

        # Create a new file (unstaged)
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file\ndef hello():\n    print('Hello')")

        # Get diff for current changes
        diff = get_git_diff_for_commit(project_dir)

        assert diff is not None
        assert "test.py" in diff
        assert "def hello():" in diff

    def test_get_branch_diff(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test get_branch_diff returns diff between branches."""
        _repo, project_dir = git_repo_with_commit

        # Get base branch name
        base_branch = get_current_branch_name(project_dir)

        # Create feature branch and make changes
        create_branch("feature-branch", project_dir)

        # Add file on feature branch
        feature_file = project_dir / "feature.py"
        feature_file.write_text("# Feature file")
        commit_all_changes("Add feature file", project_dir)

        # Get diff between branches
        diff = get_branch_diff(project_dir, base_branch)

        assert diff != ""
        assert "feature.py" in diff
        assert "# Feature file" in diff

    def test_get_branch_diff_with_base_branch(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_branch_diff with explicit base branch."""
        _repo, project_dir = git_repo_with_commit

        # Get current branch name
        base_branch = get_current_branch_name(project_dir)

        # Create feature branch (also checks it out)
        create_branch("feature", project_dir)

        # Add file
        feature_file = project_dir / "feature.py"
        feature_file.write_text("# Feature")
        commit_all_changes("Add feature", project_dir)

        # Get diff with explicit base branch
        diff = get_branch_diff(project_dir, base_branch=base_branch)

        assert diff != ""
        assert "feature.py" in diff
