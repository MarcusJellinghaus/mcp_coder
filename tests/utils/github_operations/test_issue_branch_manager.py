"""Unit tests for IssueBranchManager and branch name generation utilities."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.utils.github_operations.issue_branch_manager import (
    IssueBranchManager,
    generate_branch_name_from_issue,
)


class TestBranchNameGeneration:
    """Test suite for branch name generation utility function."""

    def test_basic_sanitization(self) -> None:
        """Test basic branch name generation with simple title."""
        result = generate_branch_name_from_issue(123, "Add New Feature")
        assert result == "123-add-new-feature"

    def test_dash_conversion(self) -> None:
        """Test that ' - ' is converted to '---' (GitHub-specific rule)."""
        result = generate_branch_name_from_issue(456, "Add New Feature - Part 1")
        assert result == "456-add-new-feature---part-1"

    def test_lowercase(self) -> None:
        """Test that all characters are converted to lowercase."""
        result = generate_branch_name_from_issue(789, "FIX BUG IN MODULE")
        assert result == "789-fix-bug-in-module"

    def test_alphanumeric_only(self) -> None:
        """Test that non-alphanumeric characters (except dash) are converted to dashes."""
        result = generate_branch_name_from_issue(101, "Fix bug #42 & issue @123")
        assert result == "101-fix-bug-42-issue-123"

    def test_spaces_to_dashes(self) -> None:
        """Test that spaces are converted to dashes."""
        result = generate_branch_name_from_issue(202, "Update user interface")
        assert result == "202-update-user-interface"

    def test_strip_leading_trailing_dashes(self) -> None:
        """Test that leading and trailing dashes are stripped."""
        result = generate_branch_name_from_issue(303, "!!!Important Fix!!!")
        assert result == "303-important-fix"

    def test_truncation_preserves_issue_number(self) -> None:
        """Test that truncation keeps issue number and truncates title."""
        long_title = "A" * 300  # Very long title
        result = generate_branch_name_from_issue(404, long_title, max_length=50)

        # Should start with "404-"
        assert result.startswith("404-")
        # Should be exactly max_length characters
        assert len(result) == 50
        # Should not end with a dash
        assert not result.endswith("-")

    def test_empty_title(self) -> None:
        """Test handling of empty or whitespace-only title."""
        result = generate_branch_name_from_issue(505, "")
        assert result == "505"

        result = generate_branch_name_from_issue(606, "   ")
        assert result == "606"

    def test_special_characters(self) -> None:
        """Test handling of various special characters."""
        result = generate_branch_name_from_issue(707, "Fix: Bug! (Urgent) @user #tag")
        assert result == "707-fix-bug-urgent-user-tag"

    def test_multiple_spaces(self) -> None:
        """Test that multiple consecutive spaces are collapsed to single dash."""
        result = generate_branch_name_from_issue(808, "Fix    multiple     spaces")
        assert result == "808-fix-multiple-spaces"

    def test_unicode_characters(self) -> None:
        """Test handling of Unicode characters."""
        result = generate_branch_name_from_issue(909, "Add café and naïve handling")
        # Unicode characters should be replaced with dashes
        assert result.startswith("909-")
        # Should only contain lowercase alphanumeric and dashes
        assert all(c.isalnum() or c == "-" for c in result)

    def test_emoji_handling(self) -> None:
        """Test handling of emoji characters."""
        result = generate_branch_name_from_issue(1010, "🚀 Launch new feature 🎉")
        # Emojis should be replaced with dashes
        assert result.startswith("1010-")
        # Should only contain lowercase alphanumeric and dashes
        assert all(c.isalnum() or c == "-" for c in result)

    def test_multiple_consecutive_dashes_collapsed(self) -> None:
        """Test that multiple consecutive dashes are collapsed to single dash."""
        result = generate_branch_name_from_issue(1111, "Fix---multiple---dashes")
        assert "---" not in result or result.count("---") == 1  # Only from " - "

    def test_custom_max_length(self) -> None:
        """Test custom max_length parameter."""
        long_title = "B" * 200
        result = generate_branch_name_from_issue(1212, long_title, max_length=100)
        assert len(result) == 100
        assert result.startswith("1212-")

    def test_default_max_length(self) -> None:
        """Test default max_length of 200 characters."""
        long_title = "C" * 300
        result = generate_branch_name_from_issue(1313, long_title)
        assert len(result) == 200
        assert result.startswith("1313-")

    def test_title_with_only_special_characters(self) -> None:
        """Test title containing only special characters."""
        result = generate_branch_name_from_issue(1414, "!!!@@@###$$$")
        # Should strip all special chars and dashes, leaving only issue number
        assert result == "1414"

    def test_mixed_alphanumeric_and_special(self) -> None:
        """Test mixed alphanumeric and special characters."""
        result = generate_branch_name_from_issue(1515, "v1.2.3-beta+build.456")
        assert result == "1515-v1-2-3-beta-build-456"

    def test_preserves_numbers_in_title(self) -> None:
        """Test that numbers in the title are preserved."""
        result = generate_branch_name_from_issue(1616, "Update API v2 to v3")
        assert result == "1616-update-api-v2-to-v3"

    def test_github_dash_separator_rule(self) -> None:
        """Test GitHub's specific rule for ' - ' separator."""
        # Single occurrence
        result = generate_branch_name_from_issue(1717, "Feature A - Part 1")
        assert "---" in result

        # Multiple occurrences
        result = generate_branch_name_from_issue(1818, "A - B - C")
        assert result == "1818-a---b---c"


class TestGetLinkedBranches:
    """Test suite for IssueBranchManager.get_linked_branches() method."""

    @pytest.fixture
    def mock_manager(self) -> IssueBranchManager:
        """Create a mock IssueBranchManager for testing."""
        with (
            patch("mcp_coder.utils.github_operations.issue_branch_manager.git.Repo"),
            patch(
                "mcp_coder.utils.github_operations.issue_branch_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch("mcp_coder.utils.github_operations.issue_branch_manager.Github"),
        ):
            manager = IssueBranchManager(Path("/fake/path"))
            return manager

    def test_valid_issue_number(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches with valid issue number."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Mock GraphQL response
        mock_response = {
            "data": {
                "repository": {
                    "issue": {
                        "linkedBranches": {
                            "nodes": [
                                {"ref": {"name": "123-feature-branch"}},
                                {"ref": {"name": "123-hotfix"}},
                            ]
                        }
                    }
                }
            }
        }
        mock_manager._github_client._Github__requester = Mock()
        mock_manager._github_client._Github__requester.graphql_query = Mock(
            return_value=mock_response
        )

        # Test
        result = mock_manager.get_linked_branches(123)
        assert result == ["123-feature-branch", "123-hotfix"]

    def test_invalid_issue_number(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches with invalid issue number."""
        # Test with negative number
        result = mock_manager.get_linked_branches(-1)
        assert result == []

        # Test with zero
        result = mock_manager.get_linked_branches(0)
        assert result == []

    def test_issue_not_found(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches when issue is not found."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Mock GraphQL response with null issue
        mock_response = {"data": {"repository": {"issue": None}}}
        mock_manager._github_client._Github__requester = Mock()
        mock_manager._github_client._Github__requester.graphql_query = Mock(
            return_value=mock_response
        )

        # Test
        result = mock_manager.get_linked_branches(999)
        assert result == []

    def test_no_linked_branches(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches when issue has no linked branches."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Mock GraphQL response with empty nodes
        mock_response = {
            "data": {"repository": {"issue": {"linkedBranches": {"nodes": []}}}}
        }
        mock_manager._github_client._Github__requester = Mock()
        mock_manager._github_client._Github__requester.graphql_query = Mock(
            return_value=mock_response
        )

        # Test
        result = mock_manager.get_linked_branches(123)
        assert result == []

    def test_multiple_linked_branches(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches with multiple branches."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Mock GraphQL response with multiple branches
        mock_response = {
            "data": {
                "repository": {
                    "issue": {
                        "linkedBranches": {
                            "nodes": [
                                {"ref": {"name": "123-feature-1"}},
                                {"ref": {"name": "123-feature-2"}},
                                {"ref": {"name": "123-feature-3"}},
                            ]
                        }
                    }
                }
            }
        }
        mock_manager._github_client._Github__requester = Mock()
        mock_manager._github_client._Github__requester.graphql_query = Mock(
            return_value=mock_response
        )

        # Test
        result = mock_manager.get_linked_branches(123)
        assert result == ["123-feature-1", "123-feature-2", "123-feature-3"]
        assert len(result) == 3

    def test_graphql_error_handling(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches handles GraphQL errors gracefully."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Mock GraphQL response with malformed data
        mock_response = {"data": None}  # Malformed response
        mock_manager._github_client._Github__requester = Mock()
        mock_manager._github_client._Github__requester.graphql_query = Mock(
            return_value=mock_response
        )

        # Test
        result = mock_manager.get_linked_branches(123)
        assert result == []

    def test_repository_not_found(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches when repository cannot be accessed."""
        # Mock _get_repository to return None
        mock_manager._repository = None
        mock_manager._get_repository = Mock(return_value=None)

        # Test
        result = mock_manager.get_linked_branches(123)
        assert result == []

    def test_null_ref_in_nodes(self, mock_manager: IssueBranchManager) -> None:
        """Test get_linked_branches handles null ref values in nodes."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Mock GraphQL response with null ref
        mock_response = {
            "data": {
                "repository": {
                    "issue": {
                        "linkedBranches": {
                            "nodes": [
                                {"ref": {"name": "123-valid-branch"}},
                                {"ref": None},  # Null ref
                                None,  # Null node
                            ]
                        }
                    }
                }
            }
        }
        mock_manager._github_client._Github__requester = Mock()
        mock_manager._github_client._Github__requester.graphql_query = Mock(
            return_value=mock_response
        )

        # Test - should skip null values and return only valid branch
        result = mock_manager.get_linked_branches(123)
        assert result == ["123-valid-branch"]
