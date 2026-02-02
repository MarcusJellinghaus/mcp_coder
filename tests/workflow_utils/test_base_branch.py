"""Tests for base branch detection functionality.

Note: Tests for detect_parent_branch_via_merge_base are located in
tests/utils/git_operations/test_readers.py to match the source structure.
"""

from collections.abc import Generator
from pathlib import Path
from typing import NamedTuple
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.workflow_utils.base_branch import detect_base_branch

# ============================================================================
# Fixtures
# ============================================================================


class GitReaderMocks(NamedTuple):
    """Container for git reader mocks."""

    branch: MagicMock  # get_current_branch_name
    extract: MagicMock  # extract_issue_number_from_branch
    default: MagicMock  # get_default_branch_name


class BaseBranchMocks(NamedTuple):
    """Consolidated mocks for base branch detection tests."""

    pr_manager: MagicMock
    issue_manager: MagicMock
    git: GitReaderMocks


@pytest.fixture
def mocks() -> Generator[BaseBranchMocks, None, None]:
    """Consolidated fixture for all base branch detection mocks.

    Note: Also patches detect_parent_branch_via_merge_base to return None,
    allowing tests to focus on PR/Issue/Default detection paths.
    """
    with (
        patch("mcp_coder.workflow_utils.base_branch.PullRequestManager") as mock_pr,
        patch("mcp_coder.workflow_utils.base_branch.IssueManager") as mock_issue,
        patch(
            "mcp_coder.workflow_utils.base_branch.get_current_branch_name"
        ) as mock_branch,
        patch(
            "mcp_coder.workflow_utils.base_branch.extract_issue_number_from_branch"
        ) as mock_extract,
        patch(
            "mcp_coder.workflow_utils.base_branch.get_default_branch_name"
        ) as mock_default,
        patch(
            "mcp_coder.workflow_utils.base_branch.detect_parent_branch_via_merge_base"
        ) as mock_merge_base,
    ):
        # By default, merge-base returns None to allow other detection methods
        mock_merge_base.return_value = None
        yield BaseBranchMocks(
            pr_manager=mock_pr,
            issue_manager=mock_issue,
            git=GitReaderMocks(
                branch=mock_branch,
                extract=mock_extract,
                default=mock_default,
            ),
        )


# ============================================================================
# Test Classes for Detection Priority (PR -> Issue -> Default)
# ============================================================================


class TestDetectBaseBranchFromPR:
    """Tests for detection from open PR."""

    def test_detect_base_branch_from_pr(self, mocks: BaseBranchMocks) -> None:
        """Test detection from open PR base branch (highest priority)."""
        # Setup: current branch has an open PR targeting 'develop'
        project_dir = Path("/test/project")
        mocks.pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature-name", "base_branch": "develop"}
        ]

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "develop"
        # PR manager should be called
        mocks.pr_manager.return_value.list_pull_requests.assert_called_once()
        # Issue manager should NOT be called when PR exists
        mocks.issue_manager.return_value.get_issue.assert_not_called()

    def test_detect_base_branch_pr_takes_priority_over_issue(
        self, mocks: BaseBranchMocks
    ) -> None:
        """Test that PR base branch has higher priority than issue base branch."""
        # Setup: both PR and issue have base branches - PR should win
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 370
        # PR targets 'develop'
        mocks.pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature-name", "base_branch": "develop"}
        ]
        # Issue specifies 'release/v2' - should be ignored
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "release/v2",
        }

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "develop"  # PR branch, not issue branch
        # Issue manager should NOT be called when PR exists
        mocks.issue_manager.return_value.get_issue.assert_not_called()


class TestDetectBaseBranchFromIssueData:
    """Tests for detection from pre-fetched issue data."""

    def test_detect_base_branch_from_issue_data(self, mocks: BaseBranchMocks) -> None:
        """Test detection from pre-fetched issue data."""
        # Setup: no PR, issue_data has base_branch
        project_dir = Path("/test/project")
        mocks.pr_manager.return_value.list_pull_requests.return_value = []

        issue_data: IssueData = {
            "number": 370,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": [],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
            "base_branch": "feature/v2",
        }

        result = detect_base_branch(
            project_dir, current_branch="370-feature", issue_data=issue_data
        )

        assert result == "feature/v2"
        # Issue manager should NOT be called when issue_data provided
        mocks.issue_manager.return_value.get_issue.assert_not_called()


class TestDetectBaseBranchFetchesIssue:
    """Tests for fetching issue when issue_data not provided."""

    def test_detect_base_branch_fetches_issue(self, mocks: BaseBranchMocks) -> None:
        """Test fetching issue when issue_data not provided."""
        # Setup: no PR, branch "123-feature", issue #123 has base_branch
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 123
        mocks.pr_manager.return_value.list_pull_requests.return_value = []
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "### Base Branch\n\nmain",
            "base_branch": "main",
        }

        result = detect_base_branch(project_dir, current_branch="123-feature")

        assert result == "main"
        mocks.issue_manager.return_value.get_issue.assert_called_once_with(123)

    def test_detect_base_branch_issue_takes_priority_over_default(
        self, mocks: BaseBranchMocks
    ) -> None:
        """Test that issue base branch has higher priority than default branch."""
        # Setup: no PR, issue has base branch, default is 'main'
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 370
        mocks.git.default.return_value = "main"
        mocks.pr_manager.return_value.list_pull_requests.return_value = []
        # Issue specifies 'release/v2'
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "release/v2",
        }

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "release/v2"  # Issue branch, not default
        # Default branch should NOT be fetched when issue has base_branch
        mocks.git.default.assert_not_called()


class TestDetectBaseBranchDefaultFallback:
    """Tests for fallback to default branch."""

    def test_detect_base_branch_default_fallback(self, mocks: BaseBranchMocks) -> None:
        """Test fallback to default branch."""
        # Setup: no PR, no issue base_branch, default branch is "main"
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 370
        mocks.git.default.return_value = "main"
        mocks.pr_manager.return_value.list_pull_requests.return_value = []
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "title": "Test Issue",
            "body": "No base branch specified",
            "base_branch": None,
        }

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "main"
        mocks.git.default.assert_called_once_with(project_dir)


class TestDetectBaseBranchReturnsNone:
    """Tests for None return value when all detection fails (was 'unknown')."""

    def test_returns_none_when_no_current_branch(self, mocks: BaseBranchMocks) -> None:
        """Detached HEAD returns None."""
        # Setup: no current branch (detached HEAD)
        project_dir = Path("/test/project")
        mocks.git.branch.return_value = None

        result = detect_base_branch(project_dir)

        assert result is None

    def test_returns_none_when_all_detection_fails(
        self, mocks: BaseBranchMocks
    ) -> None:
        """All methods fail returns None."""
        # Setup: no merge-base (via fixture), no PR, no issue base_branch, no default
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = None  # No issue number in branch
        mocks.git.default.return_value = None
        mocks.pr_manager.return_value.list_pull_requests.return_value = []

        result = detect_base_branch(project_dir, current_branch="feature-no-issue")

        assert result is None


class TestDetectBaseBranchErrorHandling:
    """Tests for graceful error handling."""

    def test_detect_base_branch_pr_api_error(self, mocks: BaseBranchMocks) -> None:
        """Test graceful handling of PR API errors."""
        # Setup: PR lookup raises exception
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 370
        mocks.pr_manager.return_value.list_pull_requests.side_effect = Exception(
            "GitHub API error"
        )
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "develop",
        }

        result = detect_base_branch(project_dir, current_branch="370-feature")

        # Should continue to issue detection
        assert result == "develop"

    def test_detect_base_branch_issue_api_error(self, mocks: BaseBranchMocks) -> None:
        """Test graceful handling of issue API errors."""
        # Setup: Issue lookup raises exception
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 370
        mocks.git.default.return_value = "main"
        mocks.pr_manager.return_value.list_pull_requests.return_value = []
        mocks.issue_manager.return_value.get_issue.side_effect = Exception(
            "GitHub API error"
        )

        result = detect_base_branch(project_dir, current_branch="370-feature")

        # Should fall back to default branch
        assert result == "main"


class TestDetectBaseBranchEdgeCases:
    """Tests for edge cases."""

    def test_detect_base_branch_no_issue_number_in_branch(
        self, mocks: BaseBranchMocks
    ) -> None:
        """Test branch without issue number skips issue lookup."""
        # Setup: branch "feature/no-issue", no PR
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = None  # No issue number extracted
        mocks.git.default.return_value = "main"
        mocks.pr_manager.return_value.list_pull_requests.return_value = []

        result = detect_base_branch(project_dir, current_branch="feature/no-issue")

        # Should skip issue lookup and return default
        assert result == "main"
        mocks.issue_manager.return_value.get_issue.assert_not_called()

    def test_detect_base_branch_pr_for_different_branch(
        self, mocks: BaseBranchMocks
    ) -> None:
        """Test that PR for different branch is ignored."""
        # Setup: PR exists but for different branch
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 370
        mocks.git.default.return_value = "main"
        mocks.pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "other-branch", "base_branch": "develop"}
        ]
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": None,
        }

        result = detect_base_branch(project_dir, current_branch="370-feature")

        # Should use default since PR is for different branch
        assert result == "main"

    def test_detect_base_branch_issue_not_found(self, mocks: BaseBranchMocks) -> None:
        """Test when issue cannot be found."""
        # Setup: issue returns with number=0 (not found)
        project_dir = Path("/test/project")
        mocks.git.extract.return_value = 999
        mocks.git.default.return_value = "main"
        mocks.pr_manager.return_value.list_pull_requests.return_value = []
        mocks.issue_manager.return_value.get_issue.return_value = {
            "number": 0,
            "base_branch": None,
        }

        result = detect_base_branch(project_dir, current_branch="999-nonexistent")

        # Should fall back to default
        assert result == "main"

    def test_detect_base_branch_auto_detects_current_branch(
        self, mocks: BaseBranchMocks
    ) -> None:
        """Test auto-detection of current branch when not provided."""
        # Setup: auto-detect current branch
        project_dir = Path("/test/project")
        mocks.git.branch.return_value = "370-feature"
        mocks.pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature", "base_branch": "develop"}
        ]

        result = detect_base_branch(project_dir)

        assert result == "develop"
        mocks.git.branch.assert_called_once_with(project_dir)
