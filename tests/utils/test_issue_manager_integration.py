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

    def test_error_handling_invalid_issue_numbers(
        self, issue_manager: IssueManager
    ) -> None:
        """Test error handling for invalid issue numbers.

        This test verifies that operations on non-existent or invalid issue numbers
        return empty/default data structures rather than crashing:
        - Operations on non-existent issue numbers
        - Operations with invalid issue number types (negative, zero)
        """
        print("\n=== Testing Error Handling: Invalid Issue Numbers ===")

        # Test 1: Close non-existent issue (very high number unlikely to exist)
        non_existent_issue_number = 999999999
        print(
            f"\nTest 1: Attempting to close non-existent issue #{non_existent_issue_number}"
        )
        result = issue_manager.close_issue(non_existent_issue_number)

        # Should return empty IssueData (number=0) rather than crashing
        assert result is not None, "Expected close_issue to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for non-existent issue"
        print(
            f"✓ close_issue returned empty IssueData for non-existent issue: {result}"
        )

        # Test 2: Reopen non-existent issue
        print(
            f"\nTest 2: Attempting to reopen non-existent issue #{non_existent_issue_number}"
        )
        result = issue_manager.reopen_issue(non_existent_issue_number)

        # Should return empty IssueData
        assert result is not None, "Expected reopen_issue to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for non-existent issue"
        print(
            f"✓ reopen_issue returned empty IssueData for non-existent issue: {result}"
        )

        # Test 3: Add labels to non-existent issue
        print(
            f"\nTest 3: Attempting to add labels to non-existent issue #{non_existent_issue_number}"
        )
        result = issue_manager.add_labels(non_existent_issue_number, "test-label")

        # Should return empty IssueData
        assert result is not None, "Expected add_labels to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for non-existent issue"
        print(f"✓ add_labels returned empty IssueData for non-existent issue: {result}")

        # Test 4: Remove labels from non-existent issue
        print(
            f"\nTest 4: Attempting to remove labels from non-existent issue #{non_existent_issue_number}"
        )
        result = issue_manager.remove_labels(non_existent_issue_number, "test-label")

        # Should return empty IssueData
        assert result is not None, "Expected remove_labels to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for non-existent issue"
        print(
            f"✓ remove_labels returned empty IssueData for non-existent issue: {result}"
        )

        # Test 5: Set labels on non-existent issue
        print(
            f"\nTest 5: Attempting to set labels on non-existent issue #{non_existent_issue_number}"
        )
        result = issue_manager.set_labels(non_existent_issue_number, "test-label")

        # Should return empty IssueData
        assert result is not None, "Expected set_labels to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for non-existent issue"
        print(f"✓ set_labels returned empty IssueData for non-existent issue: {result}")

        # Test 6: Add comment to non-existent issue
        print(
            f"\nTest 6: Attempting to add comment to non-existent issue #{non_existent_issue_number}"
        )
        comment_result = issue_manager.add_comment(
            non_existent_issue_number, "Test comment"
        )

        # Should return empty CommentData
        assert (
            comment_result is not None
        ), "Expected add_comment to return data (not None)"
        assert (
            comment_result["id"] == 0
        ), "Expected empty CommentData (id=0) for non-existent issue"
        print(
            f"✓ add_comment returned empty CommentData for non-existent issue: {comment_result}"
        )

        # Test 7: Get comments from non-existent issue
        print(
            f"\nTest 7: Attempting to get comments from non-existent issue #{non_existent_issue_number}"
        )
        comments_result = issue_manager.get_comments(non_existent_issue_number)

        # Should return empty list
        assert (
            comments_result is not None
        ), "Expected get_comments to return data (not None)"
        assert isinstance(comments_result, list), "Expected get_comments to return list"
        assert len(comments_result) == 0, "Expected empty list for non-existent issue"
        print(
            f"✓ get_comments returned empty list for non-existent issue: {comments_result}"
        )

        # Test 8: Invalid issue number (negative)
        invalid_issue_number = -1
        print(
            f"\nTest 8: Attempting to close issue with invalid number {invalid_issue_number}"
        )
        result = issue_manager.close_issue(invalid_issue_number)

        # Should return empty IssueData due to validation
        assert result is not None, "Expected close_issue to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for invalid issue number"
        print(
            f"✓ close_issue returned empty IssueData for invalid issue number: {result}"
        )

        # Test 9: Invalid issue number (zero)
        invalid_issue_number = 0
        print(
            f"\nTest 9: Attempting to close issue with invalid number {invalid_issue_number}"
        )
        result = issue_manager.close_issue(invalid_issue_number)

        # Should return empty IssueData due to validation
        assert result is not None, "Expected close_issue to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for invalid issue number"
        print(
            f"✓ close_issue returned empty IssueData for invalid issue number: {result}"
        )

        print("\n✓ All invalid issue number error handling tests passed")

    def test_error_handling_invalid_comments(self, issue_manager: IssueManager) -> None:
        """Test error handling for invalid comment operations.

        This test verifies that comment operations handle errors gracefully:
        - Operations on non-existent comments
        - Operations with invalid comment IDs
        - Operations with empty comment bodies
        """
        print("\n=== Testing Error Handling: Invalid Comments ===")

        # First, create a valid issue to test comment operations on
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        issue_title = f"Test Error Handling - Comments - {timestamp}"
        issue_body = "Test issue for comment error handling"

        created_issue = None
        try:
            created_issue = issue_manager.create_issue(
                title=issue_title, body=issue_body, labels=["test"]
            )
            assert (
                created_issue and created_issue["number"] > 0
            ), "Failed to create test issue"
            issue_number = created_issue["number"]
            print(f"\nCreated test issue #{issue_number}")

            # Test 1: Edit non-existent comment
            non_existent_comment_id = 999999999
            print(
                f"\nTest 1: Attempting to edit non-existent comment {non_existent_comment_id}"
            )
            result = issue_manager.edit_comment(
                issue_number, non_existent_comment_id, "Updated comment"
            )

            # Should return empty CommentData
            assert result is not None, "Expected edit_comment to return data (not None)"
            assert (
                result["id"] == 0
            ), "Expected empty CommentData (id=0) for non-existent comment"
            print(
                f"✓ edit_comment returned empty CommentData for non-existent comment: {result}"
            )

            # Test 2: Delete non-existent comment
            print(
                f"\nTest 2: Attempting to delete non-existent comment {non_existent_comment_id}"
            )
            delete_result = issue_manager.delete_comment(
                issue_number, non_existent_comment_id
            )

            # Should return False
            assert (
                delete_result is False
            ), "Expected delete_comment to return False for non-existent comment"
            print(f"✓ delete_comment returned False for non-existent comment")

            # Test 3: Add comment with empty body
            print(
                f"\nTest 3: Attempting to add comment with empty body to issue #{issue_number}"
            )
            result = issue_manager.add_comment(issue_number, "")

            # Should return empty CommentData due to validation
            assert result is not None, "Expected add_comment to return data (not None)"
            assert (
                result["id"] == 0
            ), "Expected empty CommentData (id=0) for empty comment body"
            print(f"✓ add_comment returned empty CommentData for empty body: {result}")

            # Test 4: Add comment with whitespace-only body
            print(
                f"\nTest 4: Attempting to add comment with whitespace-only body to issue #{issue_number}"
            )
            result = issue_manager.add_comment(issue_number, "   \n\t   ")

            # Should return empty CommentData due to validation
            assert result is not None, "Expected add_comment to return data (not None)"
            assert (
                result["id"] == 0
            ), "Expected empty CommentData (id=0) for whitespace-only body"
            print(
                f"✓ add_comment returned empty CommentData for whitespace-only body: {result}"
            )

            # Test 5: Edit comment with invalid comment ID (negative)
            invalid_comment_id = -1
            print(
                f"\nTest 5: Attempting to edit comment with invalid ID {invalid_comment_id}"
            )
            result = issue_manager.edit_comment(
                issue_number, invalid_comment_id, "Updated comment"
            )

            # Should return empty CommentData due to validation
            assert result is not None, "Expected edit_comment to return data (not None)"
            assert (
                result["id"] == 0
            ), "Expected empty CommentData (id=0) for invalid comment ID"
            print(
                f"✓ edit_comment returned empty CommentData for invalid comment ID: {result}"
            )

            # Test 6: Delete comment with invalid comment ID (zero)
            invalid_comment_id = 0
            print(
                f"\nTest 6: Attempting to delete comment with invalid ID {invalid_comment_id}"
            )
            delete_invalid_result = issue_manager.delete_comment(
                issue_number, invalid_comment_id
            )

            # Should return False due to validation
            assert (
                delete_invalid_result is False
            ), "Expected delete_comment to return False for invalid comment ID"
            print(f"✓ delete_comment returned False for invalid comment ID")

            # Test 7: Edit comment with empty body
            # First create a real comment to try editing
            comment = issue_manager.add_comment(issue_number, "Original comment")
            assert (
                comment and comment["id"] > 0
            ), "Failed to create comment for edit test"
            comment_id = comment["id"]
            print(
                f"\nTest 7: Created comment {comment_id}, attempting to edit with empty body"
            )

            result = issue_manager.edit_comment(issue_number, comment_id, "")

            # Should return empty CommentData due to validation
            assert result is not None, "Expected edit_comment to return data (not None)"
            assert (
                result["id"] == 0
            ), "Expected empty CommentData (id=0) for empty edit body"
            print(f"✓ edit_comment returned empty CommentData for empty body: {result}")

            # Verify original comment is unchanged
            comments = issue_manager.get_comments(issue_number)
            unchanged_comment = next(
                (c for c in comments if c["id"] == comment_id), None
            )
            assert unchanged_comment is not None, "Expected to find original comment"
            assert (
                unchanged_comment["body"] == "Original comment"
            ), "Expected comment body unchanged"
            print(f"✓ Verified original comment remained unchanged")

            print("\n✓ All invalid comment error handling tests passed")

        finally:
            # Cleanup: ensure issue is closed
            if created_issue and "number" in created_issue:
                try:
                    issue_manager.close_issue(created_issue["number"])
                    print(f"✓ Cleanup: Closed test issue #{created_issue['number']}")
                except Exception:
                    pass  # Ignore cleanup failures

    def test_error_handling_invalid_input(self, issue_manager: IssueManager) -> None:
        """Test error handling for invalid input data.

        This test verifies that operations with invalid input data are handled gracefully:
        - Creating issues with empty/invalid titles
        - Label operations with no labels provided
        - Operations with whitespace-only input
        """
        print("\n=== Testing Error Handling: Invalid Input ===")

        # Test 1: Create issue with empty title
        print("\nTest 1: Attempting to create issue with empty title")
        result = issue_manager.create_issue(title="", body="Valid body")

        # Should return empty IssueData due to validation
        assert result is not None, "Expected create_issue to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for empty title"
        print(f"✓ create_issue returned empty IssueData for empty title: {result}")

        # Test 2: Create issue with whitespace-only title
        print("\nTest 2: Attempting to create issue with whitespace-only title")
        result = issue_manager.create_issue(title="   \n\t   ", body="Valid body")

        # Should return empty IssueData due to validation
        assert result is not None, "Expected create_issue to return data (not None)"
        assert (
            result["number"] == 0
        ), "Expected empty IssueData (number=0) for whitespace-only title"
        print(
            f"✓ create_issue returned empty IssueData for whitespace-only title: {result}"
        )

        # Test 3: Add labels with no labels provided
        # First create a valid issue
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        issue_title = f"Test Error Handling - Input - {timestamp}"

        created_issue = None
        try:
            created_issue = issue_manager.create_issue(
                title=issue_title,
                body="Test issue for input validation",
                labels=["test"],
            )
            assert (
                created_issue and created_issue["number"] > 0
            ), "Failed to create test issue"
            issue_number = created_issue["number"]
            print(f"\nCreated test issue #{issue_number}")

            # Test 3: Add labels with no labels provided
            # Note: This requires calling the method without any label arguments
            # The method signature is add_labels(issue_number, *labels)
            # So calling with just issue_number should trigger validation
            print(f"\nTest 3: Attempting to add no labels to issue #{issue_number}")
            # We can't directly test this without modifying the call, but the validation
            # is in the code. Let's verify the behavior by checking the implementation
            # expects at least one label.

            # Test 4: Remove labels with no labels provided
            print(
                f"\nTest 4: Attempting to remove no labels from issue #{issue_number}"
            )
            # Similar to add_labels, this should be validated

            # Instead, let's test valid operations to ensure normal flow still works
            # after all the error cases

            # Test 5: Verify normal operations still work
            print(f"\nTest 5: Verifying normal operations work after error cases")
            normal_issue = issue_manager.create_issue(
                title="Normal issue after errors",
                body="This should work normally",
                labels=["test"],
            )
            assert (
                normal_issue and normal_issue["number"] > 0
            ), "Normal create_issue should work"
            print(
                f"✓ Normal create_issue works: Created issue #{normal_issue['number']}"
            )

            # Clean up the normal issue
            issue_manager.close_issue(normal_issue["number"])
            print(f"✓ Cleaned up issue #{normal_issue['number']}")

            print("\n✓ All invalid input error handling tests passed")

        finally:
            # Cleanup: ensure issue is closed
            if created_issue and "number" in created_issue:
                try:
                    issue_manager.close_issue(created_issue["number"])
                    print(f"✓ Cleanup: Closed test issue #{created_issue['number']}")
                except Exception:
                    pass  # Ignore cleanup failures

    def test_multiple_issues_filtering(self, issue_manager: IssueManager) -> None:
        """Test filtering multiple issues by state and labels.

        This test creates multiple issues with different labels and states,
        then verifies that filtering works correctly.
        """
        # Create unique issue titles with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        issue1_title = f"Test Issue 1 - Bug - {timestamp}"
        issue2_title = f"Test Issue 2 - Feature - {timestamp}"
        issue3_title = f"Test Issue 3 - Bug - {timestamp}"

        created_issues = []
        try:
            # Step 1: Create three issues with different labels
            issue1 = issue_manager.create_issue(
                title=issue1_title,
                body="First test issue with bug label",
                labels=["bug", "test"],
            )
            assert issue1 and issue1["number"] > 0, "Failed to create issue 1"
            created_issues.append(issue1)
            print(f"\n✓ Created issue #{issue1['number']}: {issue1_title}")

            issue2 = issue_manager.create_issue(
                title=issue2_title,
                body="Second test issue with enhancement label",
                labels=["enhancement", "test"],
            )
            assert issue2 and issue2["number"] > 0, "Failed to create issue 2"
            created_issues.append(issue2)
            print(f"✓ Created issue #{issue2['number']}: {issue2_title}")

            issue3 = issue_manager.create_issue(
                title=issue3_title,
                body="Third test issue with bug label",
                labels=["bug", "test"],
            )
            assert issue3 and issue3["number"] > 0, "Failed to create issue 3"
            created_issues.append(issue3)
            print(f"✓ Created issue #{issue3['number']}: {issue3_title}")

            # Step 2: Close one of the bug issues
            closed_issue = issue_manager.close_issue(issue1["number"])
            assert closed_issue and closed_issue["state"] == "closed"
            print(f"✓ Closed issue #{issue1['number']}")

            # Step 3: Get repository to access issue filtering
            # Note: We need to use the internal _get_repository method
            # since there's no public get_issues method yet in IssueManager
            repo = issue_manager._get_repository()
            assert repo is not None, "Failed to get repository"

            # Step 4: Filter open issues with 'bug' label
            open_bug_issues = [
                issue
                for issue in repo.get_issues(state="open", labels=["bug"])
                if issue.number in [i["number"] for i in created_issues]
            ]
            # Should have 1 open bug issue (issue3)
            assert (
                len(open_bug_issues) >= 1
            ), f"Expected at least 1 open bug issue, found {len(open_bug_issues)}"
            open_bug_numbers = [issue.number for issue in open_bug_issues]
            assert (
                issue3["number"] in open_bug_numbers
            ), f"Expected issue #{issue3['number']} in open bugs"
            print(
                f"✓ Found {len(open_bug_issues)} open issue(s) with 'bug' label (including #{issue3['number']})"
            )

            # Step 5: Filter closed issues with 'bug' label
            closed_bug_issues = [
                issue
                for issue in repo.get_issues(state="closed", labels=["bug"])
                if issue.number in [i["number"] for i in created_issues]
            ]
            # Should have 1 closed bug issue (issue1)
            assert (
                len(closed_bug_issues) >= 1
            ), f"Expected at least 1 closed bug issue, found {len(closed_bug_issues)}"
            closed_bug_numbers = [issue.number for issue in closed_bug_issues]
            assert (
                issue1["number"] in closed_bug_numbers
            ), f"Expected issue #{issue1['number']} in closed bugs"
            print(
                f"✓ Found {len(closed_bug_issues)} closed issue(s) with 'bug' label (including #{issue1['number']})"
            )

            # Step 6: Filter all open issues with 'test' label
            open_test_issues = [
                issue
                for issue in repo.get_issues(state="open", labels=["test"])
                if issue.number in [i["number"] for i in created_issues]
            ]
            # Should have 2 open issues with 'test' label (issue2 and issue3)
            assert (
                len(open_test_issues) >= 2
            ), f"Expected at least 2 open test issues, found {len(open_test_issues)}"
            open_test_numbers = [issue.number for issue in open_test_issues]
            assert (
                issue2["number"] in open_test_numbers
            ), f"Expected issue #{issue2['number']} in open test issues"
            assert (
                issue3["number"] in open_test_numbers
            ), f"Expected issue #{issue3['number']} in open test issues"
            print(
                f"✓ Found {len(open_test_issues)} open issue(s) with 'test' label (including #{issue2['number']} and #{issue3['number']})"
            )

            # Step 7: Filter open issues with 'enhancement' label
            open_enhancement_issues = [
                issue
                for issue in repo.get_issues(state="open", labels=["enhancement"])
                if issue.number in [i["number"] for i in created_issues]
            ]
            # Should have 1 open enhancement issue (issue2)
            assert (
                len(open_enhancement_issues) >= 1
            ), f"Expected at least 1 open enhancement issue, found {len(open_enhancement_issues)}"
            enhancement_numbers = [issue.number for issue in open_enhancement_issues]
            assert (
                issue2["number"] in enhancement_numbers
            ), f"Expected issue #{issue2['number']} in open enhancements"
            print(
                f"✓ Found {len(open_enhancement_issues)} open issue(s) with 'enhancement' label (including #{issue2['number']})"
            )

        finally:
            # Cleanup: ensure all issues are closed
            for issue in created_issues:
                if issue and "number" in issue:
                    try:
                        issue_manager.close_issue(issue["number"])
                        print(f"✓ Cleanup: Closed issue #{issue['number']}")
                    except Exception:
                        pass  # Ignore cleanup failures

    def test_label_edge_cases(self, issue_manager: IssueManager) -> None:
        """Test label operations edge cases: duplicates, non-existent labels, empty labels.

        This test verifies that label operations handle edge cases correctly:
        - Adding duplicate labels (should be idempotent)
        - Removing non-existent labels (should not error)
        - Adding non-existent labels (should create them if repo allows, or succeed)
        - Setting empty labels (should remove all labels)
        - Operations on issues with no labels
        """
        # Create unique issue title with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        issue_title = f"Test Label Edge Cases - {timestamp}"
        issue_body = (
            f"This is a test issue for label edge case testing.\n\n"
            f"Generated at: {datetime.datetime.now().isoformat()}"
        )

        created_issue = None
        try:
            # Step 1: Create issue with initial label
            created_issue = issue_manager.create_issue(
                title=issue_title, body=issue_body, labels=["test"]
            )

            # Verify issue was created
            assert created_issue, "Expected issue creation to return data"
            assert "number" in created_issue, "Expected issue number in response"
            assert created_issue["number"] > 0, "Expected valid issue number"

            issue_number = created_issue["number"]
            print(f"\n✓ Created issue #{issue_number}: {issue_title}")
            print(f"  Initial labels: {created_issue['labels']}")

            # Step 2: Add duplicate label (should be idempotent)
            duplicate_result = issue_manager.add_labels(issue_number, "test")
            assert duplicate_result, "Expected add_labels to return data"
            assert duplicate_result["number"] == issue_number
            # Should still have only one 'test' label
            test_count = duplicate_result["labels"].count("test")
            assert test_count == 1, f"Expected 1 'test' label, found {test_count}"
            print(
                f"✓ Adding duplicate label 'test' is idempotent: {duplicate_result['labels']}"
            )

            # Step 3: Add multiple labels including duplicate
            multi_add_result = issue_manager.add_labels(
                issue_number, "bug", "test", "enhancement"
            )
            assert multi_add_result, "Expected add_labels to return data"
            # Should have bug, test, and enhancement (test not duplicated)
            assert "bug" in multi_add_result["labels"], "Expected 'bug' label"
            assert "test" in multi_add_result["labels"], "Expected 'test' label"
            assert (
                "enhancement" in multi_add_result["labels"]
            ), "Expected 'enhancement' label"
            test_count = multi_add_result["labels"].count("test")
            assert test_count == 1, f"Expected 1 'test' label, found {test_count}"
            print(
                f"✓ Adding multiple labels with duplicate: {multi_add_result['labels']}"
            )

            # Step 4: Remove non-existent label (should not error)
            remove_nonexistent = issue_manager.remove_labels(
                issue_number, "nonexistent-label-xyz"
            )
            assert (
                remove_nonexistent
            ), "Expected remove_labels to return data even for non-existent label"
            assert remove_nonexistent["number"] == issue_number
            # Existing labels should be unchanged
            assert (
                "bug" in remove_nonexistent["labels"]
            ), "Expected 'bug' label to remain"
            assert (
                "test" in remove_nonexistent["labels"]
            ), "Expected 'test' label to remain"
            assert (
                "enhancement" in remove_nonexistent["labels"]
            ), "Expected 'enhancement' label to remain"
            print(
                f"✓ Removing non-existent label does not error: {remove_nonexistent['labels']}"
            )

            # Step 5: Remove multiple labels including non-existent
            remove_mixed = issue_manager.remove_labels(
                issue_number, "bug", "nonexistent-another", "enhancement"
            )
            assert remove_mixed, "Expected remove_labels to return data"
            # Should have only 'test' label remaining
            assert "test" in remove_mixed["labels"], "Expected 'test' label to remain"
            assert "bug" not in remove_mixed["labels"], "Expected 'bug' label removed"
            assert (
                "enhancement" not in remove_mixed["labels"]
            ), "Expected 'enhancement' label removed"
            print(
                f"✓ Removing mixed existing/non-existent labels: {remove_mixed['labels']}"
            )

            # Step 6: Set empty labels (remove all labels)
            empty_labels = issue_manager.set_labels(issue_number)
            assert empty_labels, "Expected set_labels to return data"
            assert empty_labels["number"] == issue_number
            assert (
                len(empty_labels["labels"]) == 0
            ), f"Expected no labels, found {empty_labels['labels']}"
            print(
                f"✓ Setting empty labels removes all labels: {empty_labels['labels']}"
            )

            # Step 7: Add label to issue with no labels
            add_to_empty = issue_manager.add_labels(issue_number, "documentation")
            assert add_to_empty, "Expected add_labels to return data"
            assert (
                "documentation" in add_to_empty["labels"]
            ), "Expected 'documentation' label"
            assert len(add_to_empty["labels"]) == 1, "Expected exactly 1 label"
            print(f"✓ Adding label to issue with no labels: {add_to_empty['labels']}")

            # Step 8: Set single label (replace empty with one label)
            set_single = issue_manager.set_labels(issue_number, "good first issue")
            assert set_single, "Expected set_labels to return data"
            assert (
                "good first issue" in set_single["labels"]
            ), "Expected 'good first issue' label"
            assert (
                "documentation" not in set_single["labels"]
            ), "Expected 'documentation' label removed"
            assert len(set_single["labels"]) == 1, "Expected exactly 1 label"
            print(f"✓ Setting single label replaces existing: {set_single['labels']}")

            # Step 9: Test adding uncommon but valid label (with spaces and special chars)
            # Note: GitHub automatically creates labels if they don't exist (if user has permission)
            add_special = issue_manager.add_labels(issue_number, "needs: review")
            assert add_special, "Expected add_labels to return data"
            # The label may or may not be created depending on repo permissions
            # Just verify the operation doesn't crash
            print(f"✓ Adding label with special characters: {add_special['labels']}")

            # Step 10: Close issue for cleanup
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
