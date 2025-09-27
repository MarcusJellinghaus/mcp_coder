"""Tests for GitHub operations module."""

import os
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import patch

import pytest
import git

from mcp_coder.utils.github_operations import PullRequestManager


@pytest.fixture
def pr_manager(tmp_path: Path) -> Generator[PullRequestManager, None, None]:
    """Create PullRequestManager instance for testing.

    Validates GitHub configuration and gracefully skips when missing.

    Returns:
        PullRequestManager: Configured instance for testing

    Raises:
        pytest.skip: When GitHub token or test repository not configured
    """
    # Check for required GitHub configuration
    github_token = os.getenv("GITHUB_TOKEN")
    test_repo_url = os.getenv("GITHUB_TEST_REPO_URL", "https://github.com/test/repo")

    if not github_token:
        pytest.skip("GitHub token not configured (GITHUB_TOKEN environment variable)")

    if test_repo_url == "https://github.com/test/repo":
        pytest.skip(
            "Test repository URL not configured (GITHUB_TEST_REPO_URL environment variable)"
        )

    # Setup test git repo with GitHub remote
    git_dir = tmp_path / "test_repo"
    git_dir.mkdir()
    repo = git.Repo.init(git_dir)
    repo.create_remote("origin", test_repo_url)
    
    # Mock config to return token
    with patch('mcp_coder.utils.user_config.get_config_value') as mock_config:
        mock_config.return_value = github_token
        yield PullRequestManager(git_dir)


@pytest.mark.github_integration
class TestPullRequestManagerIntegration:
    """Integration tests for PullRequestManager with GitHub API."""

    def test_pr_manager_lifecycle(self, pr_manager: PullRequestManager) -> None:
        """Test complete PR lifecycle: create, get, list, close.

        This test creates a PR, retrieves it, lists PRs, and closes it.
        """
        test_branch = "test-branch-lifecycle"
        pr_title = "Test PR for Lifecycle"
        pr_body = "This is a test PR for the complete lifecycle test."

        created_pr = None
        try:
            # Create pull request
            created_pr = pr_manager.create_pull_request(
                title=pr_title,
                head_branch=test_branch,
                base_branch="main",
                body=pr_body,
            )

            # Verify PR was created
            assert created_pr, "Expected PR creation to return data"
            assert "number" in created_pr, "Expected PR number in response"
            assert "title" in created_pr, "Expected PR title in response"
            assert created_pr["title"] == pr_title, f"Expected title '{pr_title}'"

            pr_number = created_pr["number"]

            # Get specific pull request
            retrieved_pr = pr_manager.get_pull_request(pr_number)
            assert retrieved_pr, "Expected to retrieve PR data"
            assert retrieved_pr["number"] == pr_number, "Expected same PR number"
            assert retrieved_pr["title"] == pr_title, "Expected same PR title"

            # List pull requests
            pr_list = pr_manager.list_pull_requests(state="open")
            assert isinstance(pr_list, list), "Expected list of PRs"
            assert len(pr_list) > 0, "Expected at least one open PR"

            # Verify our PR is in the list
            our_pr = next((pr for pr in pr_list if pr["number"] == pr_number), None)
            assert our_pr is not None, "Expected our PR to be in the list"

            # Close pull request
            closed_pr = pr_manager.close_pull_request(pr_number)
            assert closed_pr, "Expected close operation to return data"
            assert closed_pr["number"] == pr_number, "Expected same PR number"
            assert closed_pr["state"] == "closed", "Expected PR to be closed"

        finally:
            # Cleanup: ensure PR is closed even if test fails
            if created_pr and "number" in created_pr:
                try:
                    pr_manager.close_pull_request(created_pr["number"])
                except Exception:
                    pass  # Ignore cleanup failures

    def test_direct_instantiation(self, tmp_path: Path) -> None:
        """Test direct PullRequestManager instantiation."""
        # Setup git repo
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")
        
        # Test that direct instantiation creates instance
        with patch('mcp_coder.utils.user_config.get_config_value') as mock_config:
            mock_config.return_value = "test-token"
            direct_manager = PullRequestManager(git_dir)
            assert isinstance(direct_manager, PullRequestManager)
            assert direct_manager.repository_url == "https://github.com/test/repo"
            assert direct_manager.github_token == "test-token"

    def test_manager_properties(self, pr_manager: PullRequestManager) -> None:
        """Test PullRequestManager properties."""
        # Test repository_name property
        repo_name = pr_manager.repository_name
        assert repo_name, "Expected repository name to be returned"
        assert "/" in repo_name, "Expected repository name in 'owner/repo' format"

        # Test default_branch property
        default_branch = pr_manager.default_branch
        assert default_branch, "Expected default branch to be returned"
        assert isinstance(default_branch, str), "Expected default branch to be string"

    def test_list_pull_requests_with_filters(
        self, pr_manager: PullRequestManager
    ) -> None:
        """Test listing pull requests with different filters."""
        # Test listing open PRs
        open_prs = pr_manager.list_pull_requests(state="open")
        assert isinstance(open_prs, list), "Expected list for open PRs"

        # Test listing closed PRs
        closed_prs = pr_manager.list_pull_requests(state="closed")
        assert isinstance(closed_prs, list), "Expected list for closed PRs"

        # Test listing all PRs
        all_prs = pr_manager.list_pull_requests(state="all")
        assert isinstance(all_prs, list), "Expected list for all PRs"

        # When fully implemented with real API calls, we can add more specific assertions

    def test_validation_failures(self, tmp_path: Path) -> None:
        """Test validation failures for invalid inputs."""
        # Test with None project_dir
        with pytest.raises(ValueError, match="project_dir is required"):
            PullRequestManager(None)
        
        # Test with non-existent directory
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(ValueError, match="Directory does not exist"):
            PullRequestManager(nonexistent)
        
        # Test with file instead of directory
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="Path is not a directory"):
            PullRequestManager(file_path)
        
        # Test with non-git directory
        regular_dir = tmp_path / "regular_dir"
        regular_dir.mkdir()
        with pytest.raises(ValueError, match="Directory is not a git repository"):
            PullRequestManager(regular_dir)
        
        # Setup git repo for remaining tests
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")
        
        # Create manager with mocked token for validation tests
        with patch('mcp_coder.utils.user_config.get_config_value') as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

        # Test invalid PR numbers
        assert manager._validate_pr_number(0) == False
        assert manager._validate_pr_number(-1) == False
        assert manager._validate_pr_number(1) == True
        # Note: Testing with wrong types (like strings) is skipped as it's a type error

        # Test invalid branch names
        assert manager._validate_branch_name("") == False
        assert manager._validate_branch_name("   ") == False
        assert manager._validate_branch_name("branch~name") == False
        assert manager._validate_branch_name("branch^name") == False
        assert manager._validate_branch_name("branch:name") == False
        assert manager._validate_branch_name(".branch") == False
        assert manager._validate_branch_name("branch.") == False
        assert manager._validate_branch_name("branch.lock") == False
        assert manager._validate_branch_name("valid-branch") == True
        assert manager._validate_branch_name("feature/new-feature") == True

        # Test methods with invalid inputs return empty dict/list
        # Note: These return cast TypedDict instances, so we check for empty/falsy values
        invalid_pr_result = manager.get_pull_request(-1)
        assert not invalid_pr_result
        
        invalid_close_result = manager.close_pull_request(0)
        assert not invalid_close_result
        
        invalid_create_result = manager.create_pull_request("title", "invalid~branch", "main")
        assert not invalid_create_result
        
        invalid_list_result = manager.list_pull_requests(base_branch="invalid~branch")
        expected_empty_list: List[Dict[str, Any]] = []
        assert invalid_list_result == expected_empty_list
