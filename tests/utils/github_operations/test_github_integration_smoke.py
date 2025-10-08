"""Smoke tests for GitHub API integration.

These tests verify basic connectivity and functionality with the GitHub API.
All detailed testing of our wrapper logic is in test_pr_manager.py and test_labels_manager.py.

Integration tests require GitHub configuration:

Environment Variables (recommended):
    GITHUB_TOKEN: GitHub Personal Access Token with repo scope
    GITHUB_TEST_REPO_URL: URL of test repository

Config File Alternative (~/.mcp_coder/config.toml):
    [github]
    token = "ghp_your_token_here"
    test_repo_url = "https://github.com/user/test-repo"

Note: Tests will be skipped if configuration is missing.
"""

import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

from mcp_coder.utils.github_operations import LabelsManager, PullRequestManager

if TYPE_CHECKING:
    from tests.conftest import GitHubTestSetup


@pytest.fixture
def labels_manager(
    github_test_setup: "GitHubTestSetup",
) -> Generator[LabelsManager, None, None]:
    """Create LabelsManager instance for testing."""
    from tests.conftest import create_github_manager

    try:
        manager = create_github_manager(LabelsManager, github_test_setup)
        yield manager
    except Exception as e:
        pytest.skip(f"Failed to create LabelsManager: {e}")


@pytest.fixture
def pr_manager(
    github_test_setup: "GitHubTestSetup",
) -> Generator[PullRequestManager, None, None]:
    """Create PullRequestManager instance for testing."""
    from tests.conftest import create_github_manager

    try:
        manager = create_github_manager(PullRequestManager, github_test_setup)
        yield manager
    except Exception as e:
        pytest.skip(f"Failed to create PullRequestManager: {e}")


@pytest.mark.github_integration
class TestPullRequestManagerSmoke:
    """Smoke test for PullRequestManager GitHub API integration."""

    def test_basic_api_connectivity(self, pr_manager: PullRequestManager) -> None:
        """Smoke test: Verify basic GitHub API connectivity for PR operations.

        This is a minimal integration test that verifies:
        1. Authentication works
        2. Repository access works
        3. Basic PR listing works

        Detailed functionality testing is in test_pr_manager.py with mocked APIs.
        """
        # Test that we can list PRs (tests auth + repo access)
        open_prs = pr_manager.list_pull_requests(state="open")
        assert isinstance(open_prs, list), "Expected list for open PRs"

        closed_prs = pr_manager.list_pull_requests(state="closed")
        assert isinstance(closed_prs, list), "Expected list for closed PRs"

        # Verify manager properties work
        repo_name = pr_manager.repository_name
        assert repo_name, "Expected repository name"
        assert "/" in repo_name, "Expected repository name in 'owner/repo' format"

    def test_pr_crud_lifecycle(self, pr_manager: PullRequestManager) -> None:
        """Smoke test: Verify full PR CRUD lifecycle with real GitHub API.

        This test verifies:
        1. Branch creation and commit works
        2. PR creation works
        3. PR retrieval works
        4. PR closing works

        This is the minimal end-to-end test for PR operations.
        """
        import git

        from mcp_coder.utils.git_operations import (
            branch_exists,
            checkout_branch,
            create_branch,
            delete_branch,
        )

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        test_branch = f"smoke-test-pr-{timestamp}"
        pr_title = f"Smoke test PR - {timestamp}"
        pr_body = "Automated smoke test for PR CRUD operations"

        repo = git.Repo(pr_manager.project_dir)
        original_branch = repo.active_branch.name
        created_pr = None

        try:
            # Create branch
            if not branch_exists(pr_manager.project_dir, test_branch):
                create_branch(test_branch, pr_manager.project_dir, from_branch="main")

            checkout_branch(test_branch, pr_manager.project_dir)

            # Create commit
            test_file = pr_manager.project_dir / f"smoke_test_{timestamp}.txt"
            test_file.write_text(f"Smoke test at {timestamp}\n")
            repo.index.add([str(test_file)])
            repo.index.commit(f"Smoke test commit {timestamp}")

            # Push branch
            repo.git.push("--set-upstream", "origin", test_branch)

            # Create PR
            created_pr = pr_manager.create_pull_request(
                title=pr_title,
                head_branch=test_branch,
                base_branch="main",
                body=pr_body,
            )
            assert created_pr, "Expected PR creation to return data"
            assert created_pr["number"] > 0, "Expected valid PR number"

            pr_number = created_pr["number"]
            print(f"\n[OK] Created PR #{pr_number}: {created_pr['url']}")

            # Read PR
            retrieved_pr = pr_manager.get_pull_request(pr_number)
            assert retrieved_pr["number"] == pr_number
            assert retrieved_pr["title"] == pr_title

            # Close PR
            closed_pr = pr_manager.close_pull_request(pr_number)
            assert closed_pr["state"] == "closed"
            print(
                f"[OK] Closed PR #{pr_number} - Check closed PRs in your repo to verify!"
            )

        finally:
            # Cleanup
            if created_pr and "number" in created_pr:
                try:
                    pr_manager.close_pull_request(created_pr["number"])
                except Exception:
                    pass

            # Switch back to original branch and delete test branch
            try:
                repo.git.checkout(original_branch)
                # Delete the test branch locally and remotely
                delete_branch(
                    test_branch, pr_manager.project_dir, force=True, delete_remote=True
                )
                print(f"[OK] Cleaned up test branch: {test_branch}")
            except Exception as e:
                print(f"[WARN] Branch cleanup failed: {e}")


@pytest.mark.github_integration
class TestLabelsManagerSmoke:
    """Smoke test for LabelsManager GitHub API integration."""

    def test_basic_api_connectivity(self, labels_manager: LabelsManager) -> None:
        """Smoke test: Verify basic GitHub API connectivity for label operations.

        This is a minimal integration test that verifies:
        1. Authentication works
        2. Repository access works
        3. Basic label listing works
        4. CRUD operations work end-to-end

        Detailed functionality testing is in test_labels_manager.py with mocked APIs.
        """
        # Test that we can list labels (tests auth + repo access)
        labels_list = labels_manager.get_labels()
        assert isinstance(labels_list, list), "Expected list of labels"

        # Quick CRUD test with one label
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        label_name = f"smoke-test-{timestamp}"

        created_label = None
        try:
            # Create
            created_label = labels_manager.create_label(
                name=label_name, color="FF0000", description="Smoke test label"
            )
            assert created_label, "Expected label creation to return data"
            assert created_label["name"] == label_name

            # Read
            retrieved_label = labels_manager.get_label(label_name)
            assert retrieved_label["name"] == label_name

            # Update
            updated_label = labels_manager.update_label(name=label_name, color="00FF00")
            assert updated_label["color"] == "00FF00"

            # Delete
            delete_result = labels_manager.delete_label(label_name)
            assert delete_result is True

        finally:
            # Cleanup
            if created_label and "name" in created_label:
                try:
                    labels_manager.delete_label(created_label["name"])
                except Exception:
                    pass  # Ignore cleanup failures
