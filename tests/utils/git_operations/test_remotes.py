"""Minimal tests for git remote operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import get_github_repository_url, git_push


@pytest.mark.git_integration
class TestRemoteOperations:
    """Minimal tests for remote operations."""

    def test_get_github_repository_url(self, git_repo: tuple[Repo, Path]) -> None:
        """Test get_github_repository_url extracts GitHub URL."""
        repo, project_dir = git_repo

        # Add GitHub remote
        repo.create_remote("origin", "https://github.com/user/repo.git")

        # Get GitHub URL
        url = get_github_repository_url(project_dir)

        assert url == "https://github.com/user/repo"

    def test_get_github_repository_url_with_ssh(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_github_repository_url handles SSH URLs."""
        repo, project_dir = git_repo

        # Add GitHub remote with SSH URL
        repo.create_remote("origin", "git@github.com:user/repo.git")

        # Get GitHub URL
        url = get_github_repository_url(project_dir)

        assert url == "https://github.com/user/repo"

    def test_get_github_repository_url_no_remote(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_github_repository_url returns None without remote."""
        _repo, project_dir = git_repo

        # No remote configured
        url = get_github_repository_url(project_dir)

        assert url is None


@pytest.mark.git_integration
class TestGitPushForceWithLease:
    """Tests for git_push with force_with_lease parameter."""

    def test_git_push_default_no_force(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test default push without force flag."""
        repo, project_dir, _bare_remote = git_repo_with_remote

        # Push the main branch to remote first
        repo.git.push("--set-upstream", "origin", "master")

        # Create a new commit
        readme = project_dir / "README.md"
        readme.write_text("# Test Project\n\nUpdated content")
        repo.index.add(["README.md"])
        repo.index.commit("Second commit")

        # Push using git_push with default force_with_lease=False
        result = git_push(project_dir)

        assert result["success"] is True
        assert result["error"] is None

    def test_git_push_force_with_lease_after_rebase(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test force push with lease succeeds after rebase."""
        repo, project_dir, _bare_remote = git_repo_with_remote

        # Push initial state to remote
        repo.git.push("--set-upstream", "origin", "master")

        # Create local commit
        readme = project_dir / "README.md"
        readme.write_text("# Test Project\n\nLocal changes")
        repo.index.add(["README.md"])
        repo.index.commit("Local commit")

        # Push local commit
        repo.git.push("origin", "master")

        # Simulate rebase by amending the commit (creates diverged history)
        # First, reset to before our commit
        repo.git.reset("--soft", "HEAD~1")

        # Create a new commit with different message (simulating rebased commit)
        readme.write_text("# Test Project\n\nLocal changes (rebased)")
        repo.index.add(["README.md"])
        repo.index.commit("Local commit (rebased)")

        # Regular push would fail, but force_with_lease should succeed
        # because our local ref matches what we expect the remote to be
        result = git_push(project_dir, force_with_lease=True)

        assert result["success"] is True
        assert result["error"] is None

    def test_git_push_force_with_lease_fails_on_unexpected_remote(
        self, git_repo_with_remote: tuple[Repo, Path, Path], tmp_path: Path
    ) -> None:
        """Test force with lease fails if remote has unexpected commits."""
        repo, project_dir, bare_remote = git_repo_with_remote

        # Push initial state to remote
        repo.git.push("--set-upstream", "origin", "master")

        # Clone the repo to another location to simulate another developer
        other_clone_dir = tmp_path / "other_clone"
        other_repo = Repo.clone_from(str(bare_remote), str(other_clone_dir))

        # Configure git user in other clone
        with other_repo.config_writer() as config:
            config.set_value("user", "name", "Other User")
            config.set_value("user", "email", "other@example.com")

        # Make and push a commit from the other clone (simulating another developer)
        other_readme = other_clone_dir / "README.md"
        other_readme.write_text("# Test Project\n\nOther developer changes")
        other_repo.index.add(["README.md"])
        other_repo.index.commit("Other developer commit")
        other_repo.git.push("origin", "master")

        # Now in our original repo, make a local commit without fetching
        readme = project_dir / "README.md"
        readme.write_text("# Test Project\n\nOur local changes")
        repo.index.add(["README.md"])
        repo.index.commit("Our local commit")

        # force_with_lease should fail because remote has unexpected commits
        result = git_push(project_dir, force_with_lease=True)

        # Should fail safely
        assert result["success"] is False
        assert result["error"] is not None
