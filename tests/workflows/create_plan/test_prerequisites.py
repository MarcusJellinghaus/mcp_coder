"""Tests for create_plan workflow prerequisites validation functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from workflows.create_plan import check_prerequisites


class TestCheckPrerequisites:
    """Test check_prerequisites function."""

    def test_check_prerequisites_success(self, tmp_path: Path) -> None:
        """Test check_prerequisites with clean repo and valid issue."""
        # Create mock issue data
        mock_issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test issue body",
            state="open",
            labels=["bug"],
            assignees=["testuser"],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        # Mock is_working_directory_clean to return True
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=True
        ):
            # Mock IssueManager
            with patch("workflows.create_plan.IssueManager") as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_issue.return_value = mock_issue_data
                mock_manager_class.return_value = mock_manager

                success, issue_data = check_prerequisites(tmp_path, 123)

        assert success is True
        assert issue_data["number"] == 123
        assert issue_data["title"] == "Test Issue"
        assert issue_data["body"] == "Test issue body"
        assert issue_data["state"] == "open"

    def test_check_prerequisites_dirty_repo(self, tmp_path: Path) -> None:
        """Test check_prerequisites with dirty repository."""
        # Mock is_working_directory_clean to return False
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=False
        ):
            success, issue_data = check_prerequisites(tmp_path, 123)

        assert success is False
        assert issue_data["number"] == 0
        assert issue_data["title"] == ""
        assert issue_data["body"] == ""
        assert issue_data["state"] == ""

    def test_check_prerequisites_issue_not_found(self, tmp_path: Path) -> None:
        """Test check_prerequisites when issue is not found."""
        # Create empty issue data (number == 0 indicates not found)
        empty_issue_data = IssueData(
            number=0,
            title="",
            body="",
            state="",
            labels=[],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="",
            locked=False,
        )

        # Mock is_working_directory_clean to return True
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=True
        ):
            # Mock IssueManager to return empty issue data
            with patch("workflows.create_plan.IssueManager") as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_issue.return_value = empty_issue_data
                mock_manager_class.return_value = mock_manager

                success, issue_data = check_prerequisites(tmp_path, 999)

        assert success is False
        assert issue_data["number"] == 0
        assert issue_data["title"] == ""

    def test_check_prerequisites_github_api_error(self, tmp_path: Path) -> None:
        """Test check_prerequisites when GitHub API throws an error."""
        # Mock is_working_directory_clean to return True
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=True
        ):
            # Mock IssueManager to raise an exception
            with patch("workflows.create_plan.IssueManager") as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_issue.side_effect = Exception("GitHub API error")
                mock_manager_class.return_value = mock_manager

                success, issue_data = check_prerequisites(tmp_path, 123)

        assert success is False
        assert issue_data["number"] == 0
        assert issue_data["title"] == ""

    def test_check_prerequisites_logs_issue_details(self, tmp_path: Path) -> None:
        """Test check_prerequisites logs issue details on success."""
        # Create mock issue data with specific details
        mock_issue_data = IssueData(
            number=456,
            title="Feature Request: Add logging",
            body="We need better logging",
            state="open",
            labels=["enhancement"],
            assignees=[],
            user="testuser",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/456",
            locked=False,
        )

        # Mock is_working_directory_clean to return True
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=True
        ):
            # Mock IssueManager
            with patch("workflows.create_plan.IssueManager") as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_issue.return_value = mock_issue_data
                mock_manager_class.return_value = mock_manager

                # Capture logger output
                with patch("workflows.create_plan.logger") as mock_logger:
                    success, issue_data = check_prerequisites(tmp_path, 456)

                    # Verify logging calls
                    assert mock_logger.info.call_count >= 3
                    # Check for specific log messages
                    log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    assert any("Checking prerequisites" in call for call in log_calls)
                    assert any(
                        "✓ Git working directory is clean" in call for call in log_calls
                    )
                    assert any(
                        "✓ Issue #456 exists: 'Feature Request: Add logging'" in call
                        for call in log_calls
                    )
                    assert any("All prerequisites passed" in call for call in log_calls)

        assert success is True
        assert issue_data["number"] == 456
        assert issue_data["title"] == "Feature Request: Add logging"

    def test_check_prerequisites_git_value_error(self, tmp_path: Path) -> None:
        """Test check_prerequisites when is_working_directory_clean raises ValueError."""
        # Mock is_working_directory_clean to raise ValueError
        with patch(
            "workflows.create_plan.is_working_directory_clean",
            side_effect=ValueError("Not a git repository"),
        ):
            success, issue_data = check_prerequisites(tmp_path, 123)

        assert success is False
        assert issue_data["number"] == 0

    def test_check_prerequisites_git_unexpected_error(self, tmp_path: Path) -> None:
        """Test check_prerequisites when is_working_directory_clean raises unexpected error."""
        # Mock is_working_directory_clean to raise unexpected error
        with patch(
            "workflows.create_plan.is_working_directory_clean",
            side_effect=RuntimeError("Unexpected error"),
        ):
            success, issue_data = check_prerequisites(tmp_path, 123)

        assert success is False
        assert issue_data["number"] == 0

    def test_check_prerequisites_issue_manager_initialization_error(
        self, tmp_path: Path
    ) -> None:
        """Test check_prerequisites when IssueManager initialization fails."""
        # Mock is_working_directory_clean to return True
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=True
        ):
            # Mock IssueManager initialization to raise an exception
            with patch(
                "workflows.create_plan.IssueManager",
                side_effect=ValueError("Invalid configuration"),
            ):
                success, issue_data = check_prerequisites(tmp_path, 123)

        assert success is False
        assert issue_data["number"] == 0

    def test_check_prerequisites_returns_complete_issue_data(
        self, tmp_path: Path
    ) -> None:
        """Test check_prerequisites returns complete IssueData with all fields."""
        # Create complete mock issue data with all fields populated
        mock_issue_data = IssueData(
            number=789,
            title="Complete Issue Data Test",
            body="This is a complete test issue with all fields",
            state="open",
            labels=["bug", "high-priority", "needs-review"],
            assignees=["user1", "user2"],
            user="issue_creator",
            created_at="2024-01-01T12:00:00",
            updated_at="2024-01-15T14:30:00",
            url="https://github.com/test/repo/issues/789",
            locked=False,
        )

        # Mock is_working_directory_clean to return True
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=True
        ):
            # Mock IssueManager
            with patch("workflows.create_plan.IssueManager") as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_issue.return_value = mock_issue_data
                mock_manager_class.return_value = mock_manager

                success, issue_data = check_prerequisites(tmp_path, 789)

        # Verify all fields are correctly returned
        assert success is True
        assert issue_data["number"] == 789
        assert issue_data["title"] == "Complete Issue Data Test"
        assert issue_data["body"] == "This is a complete test issue with all fields"
        assert issue_data["state"] == "open"
        assert issue_data["labels"] == ["bug", "high-priority", "needs-review"]
        assert issue_data["assignees"] == ["user1", "user2"]
        assert issue_data["user"] == "issue_creator"
        assert issue_data["created_at"] == "2024-01-01T12:00:00"
        assert issue_data["updated_at"] == "2024-01-15T14:30:00"
        assert issue_data["url"] == "https://github.com/test/repo/issues/789"
        assert issue_data["locked"] is False

    def test_check_prerequisites_empty_issue_data_structure(
        self, tmp_path: Path
    ) -> None:
        """Test check_prerequisites returns correctly structured empty IssueData on failure."""
        # Mock is_working_directory_clean to return False
        with patch(
            "workflows.create_plan.is_working_directory_clean", return_value=False
        ):
            success, issue_data = check_prerequisites(tmp_path, 123)

        # Verify empty IssueData has correct structure
        assert success is False
        assert issue_data["number"] == 0
        assert issue_data["title"] == ""
        assert issue_data["body"] == ""
        assert issue_data["state"] == ""
        assert issue_data["labels"] == []
        assert issue_data["assignees"] == []
        assert issue_data["user"] is None
        assert issue_data["created_at"] is None
        assert issue_data["updated_at"] is None
        assert issue_data["url"] == ""
        assert issue_data["locked"] is False
