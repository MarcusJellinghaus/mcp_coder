"""Integration tests for IssueManager with GitHub API.

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

from mcp_coder.utils.github_operations.issue_manager import IssueManager

if TYPE_CHECKING:
    from tests.conftest import GitHubTestSetup


@pytest.fixture
def issue_manager(
    github_test_setup: "GitHubTestSetup",
) -> Generator[IssueManager, None, None]:
    """Create IssueManager instance for testing.

    Uses shared github_test_setup fixture for configuration and repository setup.

    Args:
        github_test_setup: Shared GitHub test configuration fixture

    Returns:
        IssueManager: Configured instance for testing

    Raises:
        pytest.skip: When GitHub token or test repository not configured
    """
    from tests.conftest import create_github_manager

    try:
        manager = create_github_manager(IssueManager, github_test_setup)
        yield manager
    except Exception as e:
        pytest.skip(f"Failed to create IssueManager: {e}")


@pytest.mark.github_integration
class TestIssueManagerIntegration:
    """Integration tests for IssueManager with GitHub API."""

    def test_issue_lifecycle(self, issue_manager: IssueManager) -> None:
        """Test complete issue lifecycle: create → get → close → reopen.

        This test creates an issue, retrieves it, closes it, and reopens it.
        The issue is cleaned up (closed) at the end.
        """
        # Create unique issue title with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        issue_title = f"Test Issue Lifecycle - {timestamp}"
        issue_body = (
            f"This is a test issue for lifecycle testing.\n\n"
            f"Generated at: {datetime.datetime.now().isoformat()}"
        )

        created_issue = None
        try:
            # Step 1: Create issue
            created_issue = issue_manager.create_issue(
                title=issue_title, body=issue_body, labels=["test"]
            )

            # Verify issue was created
            assert created_issue, "Expected issue creation to return data"
            assert "number" in created_issue, "Expected issue number in response"
            assert created_issue["number"] > 0, "Expected valid issue number"
            assert (
                created_issue["title"] == issue_title
            ), f"Expected title '{issue_title}'"
            assert created_issue["body"] == issue_body, "Expected matching body"
            assert created_issue["state"] == "open", "Expected issue to be open"
            assert "test" in created_issue["labels"], "Expected 'test' label"

            issue_number = created_issue["number"]
            print(f"\n✓ Created issue #{issue_number}: {issue_title}")

            # Step 2: Close issue
            closed_issue = issue_manager.close_issue(issue_number)

            # Verify issue was closed
            assert closed_issue, "Expected close operation to return data"
            assert closed_issue["number"] == issue_number, "Expected same issue number"
            assert closed_issue["state"] == "closed", "Expected issue to be closed"
            print(f"✓ Closed issue #{issue_number}")

            # Step 3: Reopen issue
            reopened_issue = issue_manager.reopen_issue(issue_number)

            # Verify issue was reopened
            assert reopened_issue, "Expected reopen operation to return data"
            assert (
                reopened_issue["number"] == issue_number
            ), "Expected same issue number"
            assert reopened_issue["state"] == "open", "Expected issue to be open"
            print(f"✓ Reopened issue #{issue_number}")

            # Step 4: Test label operations
            # Add labels
            labeled_issue = issue_manager.add_labels(issue_number, "bug", "enhancement")
            assert labeled_issue, "Expected add_labels to return data"
            assert labeled_issue["number"] == issue_number, "Expected same issue number"
            assert "bug" in labeled_issue["labels"], "Expected 'bug' label"
            assert (
                "enhancement" in labeled_issue["labels"]
            ), "Expected 'enhancement' label"
            assert "test" in labeled_issue["labels"], "Expected 'test' label to remain"
            print(f"✓ Added labels to issue #{issue_number}: {labeled_issue['labels']}")

            # Remove labels
            removed_label_issue = issue_manager.remove_labels(issue_number, "bug")
            assert removed_label_issue, "Expected remove_labels to return data"
            assert (
                removed_label_issue["number"] == issue_number
            ), "Expected same issue number"
            assert (
                "bug" not in removed_label_issue["labels"]
            ), "Expected 'bug' label removed"
            assert (
                "enhancement" in removed_label_issue["labels"]
            ), "Expected 'enhancement' label to remain"
            assert (
                "test" in removed_label_issue["labels"]
            ), "Expected 'test' label to remain"
            print(
                f"✓ Removed label from issue #{issue_number}: {removed_label_issue['labels']}"
            )

            # Set labels (replace all existing labels)
            set_label_issue = issue_manager.set_labels(
                issue_number, "documentation", "good first issue"
            )
            assert set_label_issue, "Expected set_labels to return data"
            assert (
                set_label_issue["number"] == issue_number
            ), "Expected same issue number"
            assert (
                "documentation" in set_label_issue["labels"]
            ), "Expected 'documentation' label"
            assert (
                "good first issue" in set_label_issue["labels"]
            ), "Expected 'good first issue' label"
            assert (
                "bug" not in set_label_issue["labels"]
            ), "Expected 'bug' label removed"
            assert (
                "enhancement" not in set_label_issue["labels"]
            ), "Expected 'enhancement' label removed"
            assert (
                "test" not in set_label_issue["labels"]
            ), "Expected 'test' label removed"
            assert (
                len(set_label_issue["labels"]) == 2
            ), "Expected exactly 2 labels after set_labels"
            print(f"✓ Set labels on issue #{issue_number}: {set_label_issue['labels']}")

            # Step 5: Close issue again for cleanup
            final_close = issue_manager.close_issue(issue_number)
            assert final_close, "Expected final close to succeed"
            assert final_close["state"] == "closed", "Expected issue to be closed"
            print(f"✓ Final cleanup: Closed issue #{issue_number}")

        finally:
            # Cleanup: ensure issue is closed even if test fails
            if created_issue and "number" in created_issue:
                try:
                    issue_manager.close_issue(created_issue["number"])
                    print(
                        f"✓ Cleanup: Ensured issue #{created_issue['number']} is closed"
                    )
                except Exception:
                    pass  # Ignore cleanup failures

    def test_comment_operations(self, issue_manager: IssueManager) -> None:
        """Test comment operations: add → get → edit → delete.

        This test creates an issue, adds a comment, edits it, and deletes it.
        The issue is cleaned up (closed) at the end.
        """
        # Create unique issue title with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        issue_title = f"Test Comment Operations - {timestamp}"
        issue_body = (
            f"This is a test issue for comment operations.\n\n"
            f"Generated at: {datetime.datetime.now().isoformat()}"
        )

        created_issue = None
        try:
            # Step 1: Create issue
            created_issue = issue_manager.create_issue(
                title=issue_title, body=issue_body, labels=["test"]
            )

            # Verify issue was created
            assert created_issue, "Expected issue creation to return data"
            assert "number" in created_issue, "Expected issue number in response"
            assert created_issue["number"] > 0, "Expected valid issue number"

            issue_number = created_issue["number"]
            print(f"\n✓ Created issue #{issue_number}: {issue_title}")

            # Step 2: Add comment
            comment_body = "This is a test comment"
            added_comment = issue_manager.add_comment(issue_number, comment_body)

            # Verify comment was added
            assert added_comment, "Expected add_comment to return data"
            assert "id" in added_comment, "Expected comment ID in response"
            assert added_comment["id"] > 0, "Expected valid comment ID"
            assert (
                added_comment["body"] == comment_body
            ), "Expected matching comment body"

            comment_id = added_comment["id"]
            print(
                f"✓ Added comment {comment_id} to issue #{issue_number}: {comment_body}"
            )

            # Step 3: Get comments and verify
            comments = issue_manager.get_comments(issue_number)

            # Verify comments were retrieved
            assert comments, "Expected get_comments to return list"
            assert len(comments) >= 1, "Expected at least one comment"
            comment_ids = [c["id"] for c in comments]
            assert (
                comment_id in comment_ids
            ), f"Expected comment {comment_id} in retrieved comments"

            # Find our comment in the list
            our_comment = next((c for c in comments if c["id"] == comment_id), None)
            assert our_comment is not None, "Expected to find our comment"
            assert our_comment["body"] == comment_body, "Expected matching comment body"
            print(f"✓ Retrieved {len(comments)} comment(s) from issue #{issue_number}")

            # Step 4: Edit comment
            updated_body = "This is an updated test comment"
            edited_comment = issue_manager.edit_comment(
                issue_number, comment_id, updated_body
            )

            # Verify comment was edited
            assert edited_comment, "Expected edit_comment to return data"
            assert edited_comment["id"] == comment_id, "Expected same comment ID"
            assert (
                edited_comment["body"] == updated_body
            ), "Expected updated comment body"
            print(
                f"✓ Edited comment {comment_id} on issue #{issue_number}: {updated_body}"
            )

            # Step 5: Verify edit by getting comments again
            comments_after_edit = issue_manager.get_comments(issue_number)
            our_comment_edited = next(
                (c for c in comments_after_edit if c["id"] == comment_id), None
            )
            assert our_comment_edited is not None, "Expected to find our edited comment"
            assert (
                our_comment_edited["body"] == updated_body
            ), "Expected updated body in retrieved comment"
            print(f"✓ Verified comment {comment_id} was updated")

            # Step 6: Delete comment
            delete_result = issue_manager.delete_comment(issue_number, comment_id)

            # Verify comment was deleted
            assert delete_result is True, "Expected delete_comment to return True"
            print(f"✓ Deleted comment {comment_id} from issue #{issue_number}")

            # Step 7: Verify deletion by getting comments again
            comments_after_delete = issue_manager.get_comments(issue_number)
            comment_ids_after = [c["id"] for c in comments_after_delete]
            assert (
                comment_id not in comment_ids_after
            ), f"Expected comment {comment_id} to be deleted"
            print(f"✓ Verified comment {comment_id} was deleted")

        finally:
            # Cleanup: ensure issue is closed even if test fails
            if created_issue and "number" in created_issue:
                try:
                    issue_manager.close_issue(created_issue["number"])
                    print(
                        f"✓ Cleanup: Ensured issue #{created_issue['number']} is closed"
                    )
                except Exception:
                    pass  # Ignore cleanup failures
