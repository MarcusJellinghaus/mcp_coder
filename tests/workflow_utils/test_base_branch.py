"""Tests for base branch detection functionality."""

from collections.abc import Generator
from pathlib import Path
from typing import Tuple, cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.workflow_utils.base_branch import detect_base_branch

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pr_manager() -> Generator[MagicMock, None, None]:
    """Mock PullRequestManager with configurable PR data."""
    with patch("mcp_coder.workflow_utils.base_branch.PullRequestManager") as mock:
        yield mock


@pytest.fixture
def mock_issue_manager() -> Generator[MagicMock, None, None]:
    """Mock IssueManager for issue lookup."""
    with patch("mcp_coder.workflow_utils.base_branch.IssueManager") as mock:
        yield mock


@pytest.fixture
def mock_git_readers() -> Generator[Tuple[MagicMock, MagicMock, MagicMock], None, None]:
    """Mock git reader functions."""
    with (
        patch(
            "mcp_coder.workflow_utils.base_branch.get_current_branch_name"
        ) as mock_branch,
        patch(
            "mcp_coder.workflow_utils.base_branch.extract_issue_number_from_branch"
        ) as mock_extract,
        patch(
            "mcp_coder.workflow_utils.base_branch.get_default_branch_name"
        ) as mock_default,
    ):
        yield mock_branch, mock_extract, mock_default


# ============================================================================
# Test Classes for Detection Priority (PR -> Issue -> Default)
# ============================================================================


class TestDetectBaseBranchFromPR:
    """Tests for detection from open PR."""

    def test_detect_base_branch_from_pr(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test detection from open PR base branch (highest priority)."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: current branch has an open PR targeting 'develop'
        project_dir = Path("/test/project")
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature-name", "base_branch": "develop"}
        ]

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "develop"
        # PR manager should be called
        mock_pr_manager.return_value.list_pull_requests.assert_called_once()
        # Issue manager should NOT be called when PR exists
        mock_issue_manager.return_value.get_issue.assert_not_called()

    def test_detect_base_branch_pr_takes_priority_over_issue(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that PR base branch has higher priority than issue base branch."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: both PR and issue have base branches - PR should win
        project_dir = Path("/test/project")
        mock_extract.return_value = 370
        # PR targets 'develop'
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature-name", "base_branch": "develop"}
        ]
        # Issue specifies 'release/v2' - should be ignored
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "release/v2",
        }

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "develop"  # PR branch, not issue branch
        # Issue manager should NOT be called when PR exists
        mock_issue_manager.return_value.get_issue.assert_not_called()


class TestDetectBaseBranchFromIssueData:
    """Tests for detection from pre-fetched issue data."""

    def test_detect_base_branch_from_issue_data(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test detection from pre-fetched issue data."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no PR, issue_data has base_branch
        project_dir = Path("/test/project")
        mock_pr_manager.return_value.list_pull_requests.return_value = []

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
        mock_issue_manager.return_value.get_issue.assert_not_called()


class TestDetectBaseBranchFetchesIssue:
    """Tests for fetching issue when issue_data not provided."""

    def test_detect_base_branch_fetches_issue(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test fetching issue when issue_data not provided."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no PR, branch "123-feature", issue #123 has base_branch
        project_dir = Path("/test/project")
        mock_extract.return_value = 123
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "### Base Branch\n\nmain",
            "base_branch": "main",
        }

        result = detect_base_branch(project_dir, current_branch="123-feature")

        assert result == "main"
        mock_issue_manager.return_value.get_issue.assert_called_once_with(123)

    def test_detect_base_branch_issue_takes_priority_over_default(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that issue base branch has higher priority than default branch."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no PR, issue has base branch, default is 'main'
        project_dir = Path("/test/project")
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        # Issue specifies 'release/v2'
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "release/v2",
        }

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "release/v2"  # Issue branch, not default
        # Default branch should NOT be fetched when issue has base_branch
        mock_default.assert_not_called()


class TestDetectBaseBranchDefaultFallback:
    """Tests for fallback to default branch."""

    def test_detect_base_branch_default_fallback(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test fallback to default branch."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no PR, no issue base_branch, default branch is "main"
        project_dir = Path("/test/project")
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "title": "Test Issue",
            "body": "No base branch specified",
            "base_branch": None,
        }

        result = detect_base_branch(project_dir, current_branch="370-feature-name")

        assert result == "main"
        mock_default.assert_called_once_with(project_dir)


class TestDetectBaseBranchUnknownFallback:
    """Tests for unknown fallback when all detection fails."""

    def test_detect_base_branch_unknown_fallback(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test unknown fallback when all detection fails."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no current branch
        project_dir = Path("/test/project")
        mock_branch.return_value = None

        result = detect_base_branch(project_dir)

        assert result == "unknown"

    def test_detect_base_branch_unknown_when_no_default(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test unknown when no PR, no issue base, no default branch."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no PR, no issue base_branch, no default branch
        project_dir = Path("/test/project")
        mock_extract.return_value = None  # No issue number in branch
        mock_default.return_value = None
        mock_pr_manager.return_value.list_pull_requests.return_value = []

        result = detect_base_branch(project_dir, current_branch="feature-no-issue")

        assert result == "unknown"


class TestDetectBaseBranchErrorHandling:
    """Tests for graceful error handling."""

    def test_detect_base_branch_pr_api_error(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test graceful handling of PR API errors."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: PR lookup raises exception
        project_dir = Path("/test/project")
        mock_extract.return_value = 370
        mock_pr_manager.return_value.list_pull_requests.side_effect = Exception(
            "GitHub API error"
        )
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "develop",
        }

        result = detect_base_branch(project_dir, current_branch="370-feature")

        # Should continue to issue detection
        assert result == "develop"

    def test_detect_base_branch_issue_api_error(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test graceful handling of issue API errors."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: Issue lookup raises exception
        project_dir = Path("/test/project")
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_issue_manager.return_value.get_issue.side_effect = Exception(
            "GitHub API error"
        )

        result = detect_base_branch(project_dir, current_branch="370-feature")

        # Should fall back to default branch
        assert result == "main"


class TestDetectBaseBranchEdgeCases:
    """Tests for edge cases."""

    def test_detect_base_branch_no_issue_number_in_branch(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test branch without issue number skips issue lookup."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: branch "feature/no-issue", no PR
        project_dir = Path("/test/project")
        mock_extract.return_value = None  # No issue number extracted
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []

        result = detect_base_branch(project_dir, current_branch="feature/no-issue")

        # Should skip issue lookup and return default
        assert result == "main"
        mock_issue_manager.return_value.get_issue.assert_not_called()

    def test_detect_base_branch_pr_for_different_branch(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that PR for different branch is ignored."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: PR exists but for different branch
        project_dir = Path("/test/project")
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "other-branch", "base_branch": "develop"}
        ]
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": None,
        }

        result = detect_base_branch(project_dir, current_branch="370-feature")

        # Should use default since PR is for different branch
        assert result == "main"

    def test_detect_base_branch_issue_not_found(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test when issue cannot be found."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: issue returns with number=0 (not found)
        project_dir = Path("/test/project")
        mock_extract.return_value = 999
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 0,
            "base_branch": None,
        }

        result = detect_base_branch(project_dir, current_branch="999-nonexistent")

        # Should fall back to default
        assert result == "main"

    def test_detect_base_branch_auto_detects_current_branch(
        self,
        mock_pr_manager: MagicMock,
        mock_git_readers: Tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test auto-detection of current branch when not provided."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: auto-detect current branch
        project_dir = Path("/test/project")
        mock_branch.return_value = "370-feature"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature", "base_branch": "develop"}
        ]

        result = detect_base_branch(project_dir)

        assert result == "develop"
        mock_branch.assert_called_once_with(project_dir)
