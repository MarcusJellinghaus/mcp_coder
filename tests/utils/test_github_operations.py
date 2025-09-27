"""Tests for GitHub operations module."""

import os
from typing import Any, Dict

import pytest

from mcp_coder.utils.github_operations import PullRequestManager


@pytest.fixture
def pr_manager() -> PullRequestManager:
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

    return PullRequestManager(test_repo_url, github_token)


@pytest.mark.github_integration
class TestPullRequestManagerIntegration:
    """Integration tests for PullRequestManager with GitHub API."""

    def test_pr_manager_lifecycle(self, pr_manager: PullRequestManager) -> None:
        """Test complete PR lifecycle: create, get, list, close.

        This test creates a PR, retrieves it, lists PRs, and closes it.
        It should fail initially due to empty implementations.
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

            # Verify PR was created (should fail with empty implementation)
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

    def test_direct_instantiation(self, pr_manager: PullRequestManager) -> None:
        """Test direct PullRequestManager instantiation."""
        # Test that direct instantiation creates instance
        direct_manager = PullRequestManager(
            "https://github.com/test/repo", "test-token"
        )
        assert isinstance(direct_manager, PullRequestManager)
        assert direct_manager.repository_url == "https://github.com/test/repo"
        assert direct_manager.github_token == "test-token"

    def test_manager_properties(self, pr_manager: PullRequestManager) -> None:
        """Test PullRequestManager properties."""
        # Test repository_name property (should fail with empty implementation)
        repo_name = pr_manager.repository_name
        assert repo_name, "Expected repository name to be returned"
        assert "/" in repo_name, "Expected repository name in 'owner/repo' format"

        # Test default_branch property (should fail with empty implementation)
        default_branch = pr_manager.default_branch
        assert default_branch, "Expected default branch to be returned"
        assert isinstance(default_branch, str), "Expected default branch to be string"

    def test_merge_pull_request(self, pr_manager: PullRequestManager) -> None:
        """Test merging a pull request.

        Note: This test creates and immediately merges a PR, which may not
        be possible in all repositories due to branch protection rules.
        """
        test_branch = "test-branch-merge"
        pr_title = "Test PR for Merge"

        created_pr = None
        try:
            # Create pull request
            created_pr = pr_manager.create_pull_request(
                title=pr_title,
                head_branch=test_branch,
                base_branch="main",
                body="Test PR for merge functionality",
            )

            assert created_pr, "Expected PR creation to return data"
            pr_number = created_pr["number"]

            # Attempt to merge (may fail due to branch protection or missing commits)
            merge_result = pr_manager.merge_pull_request(pr_number)

            # Note: This might fail in real repos due to branch protection
            # But with empty implementation, it should return empty dict
            assert isinstance(merge_result, dict), "Expected merge result to be dict"

        finally:
            # Cleanup
            if created_pr and "number" in created_pr:
                try:
                    pr_manager.close_pull_request(created_pr["number"])
                except Exception:
                    pass

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

        # With empty implementation, all should return empty lists
        # When implemented, we can add more specific assertions

    def test_merge_pull_request_with_enhanced_parameters(
        self, pr_manager: PullRequestManager
    ) -> None:
        """Test merging a pull request with enhanced parameters."""
        test_branch = "test-branch-enhanced-merge"
        pr_title = "Test PR for Enhanced Merge"
        commit_title = "Custom merge commit title"
        commit_message = "Custom merge commit message\n\nDetailed description"

        created_pr = None
        try:
            # Create pull request
            created_pr = pr_manager.create_pull_request(
                title=pr_title,
                head_branch=test_branch,
                base_branch="main",
                body="Test PR for enhanced merge functionality",
            )

            if created_pr and "number" in created_pr:
                pr_number = created_pr["number"]

                # Test merge with all enhanced parameters
                merge_result = pr_manager.merge_pull_request(
                    pr_number=pr_number,
                    commit_title=commit_title,
                    commit_message=commit_message,
                    merge_method="squash",
                )

                # Verify merge result structure
                assert isinstance(
                    merge_result, dict
                ), "Expected merge result to be dict"

        finally:
            # Cleanup
            if created_pr and "number" in created_pr:
                try:
                    pr_manager.close_pull_request(created_pr["number"])
                except Exception:
                    pass

    def test_validation_failures(self) -> None:
        """Test validation failures for invalid inputs."""
        # Test with invalid token (should raise ValueError)
        try:
            PullRequestManager("https://github.com/test/repo", "")
            assert False, "Expected ValueError for empty token"
        except ValueError:
            pass  # Expected

        # Create manager with dummy token for validation tests
        manager = PullRequestManager("https://github.com/test/repo", "dummy-token")

        # Test invalid PR numbers
        assert manager._validate_pr_number(0) == False
        assert manager._validate_pr_number(-1) == False
        # Test with invalid type (this will cause type error but should be handled gracefully)
        try:
            result = manager._validate_pr_number("invalid")  # type: ignore
            assert result == False
        except (TypeError, AttributeError):
            pass  # Expected for invalid type
        assert manager._validate_pr_number(1) == True

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
        assert manager.get_pull_request(-1) == {}
        assert manager.close_pull_request(0) == {}
        assert manager.merge_pull_request(-1) == {}
        assert manager.create_pull_request("title", "invalid~branch", "main") == {}
        assert manager.list_pull_requests(base_branch="invalid~branch") == []

        # Test invalid merge method
        assert manager.merge_pull_request(1, merge_method="invalid") == {}
