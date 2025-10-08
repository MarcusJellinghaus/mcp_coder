"""Minimal tests for git remote operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import get_github_repository_url


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


# Note: fetch_remote, git_push, and push_branch require actual remote repositories
# and network access. These are better tested in real integration scenarios or
# with mock remotes. For minimal coverage, we trust GitPython handles these correctly
# and our wrappers just call the library functions.
