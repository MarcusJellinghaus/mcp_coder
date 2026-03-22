"""Unit tests for IssueBranchManager.get_branch_with_pr_fallback() method."""

# pylint: disable=protected-access  # Tests need to access protected members for mocking

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from github import GithubException

from mcp_coder.utils.github_operations.issues import IssueBranchManager


def _make_git_ref(ref_name: str) -> Mock:
    """Helper to build a mock GitRef object."""
    ref = Mock()
    ref.ref = ref_name
    return ref


class TestExtractPrsByStates:
    """Test suite for IssueBranchManager._extract_prs_by_states()."""

    @staticmethod
    def _make_pr_node(
        number: int, state: str, head_ref: str, is_draft: bool = False
    ) -> dict[str, Any]:
        """Helper to build a CrossReferencedEvent timeline node."""
        return {
            "__typename": "CrossReferencedEvent",
            "source": {
                "number": number,
                "state": state,
                "isDraft": is_draft,
                "headRefName": head_ref,
            },
        }

    def test_extract_prs_by_states_open_only(self) -> None:
        """Filters OPEN PRs, excludes CLOSED and MERGED."""
        timeline_items = [
            self._make_pr_node(1, "OPEN", "branch-open"),
            self._make_pr_node(2, "CLOSED", "branch-closed"),
            self._make_pr_node(3, "MERGED", "branch-merged"),
            self._make_pr_node(4, "OPEN", "branch-open-2", is_draft=True),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"OPEN"})

        assert len(result) == 2
        assert result[0]["headRefName"] == "branch-open"
        assert result[1]["headRefName"] == "branch-open-2"

    def test_extract_prs_by_states_closed_only(self) -> None:
        """Filters CLOSED PRs, excludes OPEN and MERGED."""
        timeline_items = [
            self._make_pr_node(1, "OPEN", "branch-open"),
            self._make_pr_node(2, "CLOSED", "branch-closed"),
            self._make_pr_node(3, "MERGED", "branch-merged"),
            self._make_pr_node(4, "CLOSED", "branch-closed-2"),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"CLOSED"})

        assert len(result) == 2
        assert result[0]["headRefName"] == "branch-closed"
        assert result[1]["headRefName"] == "branch-closed-2"

    def test_extract_prs_by_states_multiple_states(self) -> None:
        """Passing {"OPEN", "CLOSED"} returns both OPEN and CLOSED, excludes MERGED."""
        timeline_items = [
            self._make_pr_node(1, "OPEN", "branch-open"),
            self._make_pr_node(2, "CLOSED", "branch-closed"),
            self._make_pr_node(3, "MERGED", "branch-merged"),
        ]

        result = IssueBranchManager._extract_prs_by_states(
            timeline_items, {"OPEN", "CLOSED"}
        )

        assert len(result) == 2
        head_refs = {pr["headRefName"] for pr in result}
        assert head_refs == {"branch-open", "branch-closed"}

    def test_extract_prs_by_states_skips_non_cross_referenced(self) -> None:
        """Skips nodes that are not CrossReferencedEvent."""
        timeline_items: list[dict[str, Any]] = [
            {
                "__typename": "SomeOtherEvent",
                "source": {"state": "OPEN", "headRefName": "x"},
            },
            self._make_pr_node(1, "OPEN", "branch-open"),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"OPEN"})

        assert len(result) == 1
        assert result[0]["headRefName"] == "branch-open"

    def test_extract_prs_by_states_skips_missing_fields(self) -> None:
        """Skips nodes missing state or headRefName."""
        timeline_items = [
            {
                "__typename": "CrossReferencedEvent",
                "source": {"number": 1, "title": "Issue, not PR"},
            },
            self._make_pr_node(2, "OPEN", "branch-open"),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"OPEN"})

        assert len(result) == 1
        assert result[0]["headRefName"] == "branch-open"

    def test_extract_prs_by_states_empty_input(self) -> None:
        """Returns empty list for empty timeline items."""
        result = IssueBranchManager._extract_prs_by_states([], {"OPEN"})
        assert result == []


class TestGetBranchWithPRFallback:
    """Test suite for IssueBranchManager.get_branch_with_pr_fallback()."""

    @pytest.fixture
    def mock_manager(self) -> IssueBranchManager:
        """Create a mock IssueBranchManager for testing."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        with (
            patch(
                "mcp_coder.utils.git_operations.is_git_repository", return_value=True
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_values",
                return_value={(("github", "token")): "fake_token"},
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            manager = IssueBranchManager(mock_path)
            return manager

    def test_linked_branch_found_returns_branch_name(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test branch found via linkedBranches (primary path).

        When linkedBranches returns a branch, should return immediately
        without querying PR timeline.
        """
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return branch
        mock_manager.get_linked_branches = Mock(  # type: ignore[method-assign]
            return_value=["123-feature-branch"]
        )

        # Setup: Mock GraphQL client (should NOT be called)
        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_graphql_query = Mock()
        mock_manager._github_client._Github__requester.graphql_query = mock_graphql_query  # type: ignore[attr-defined]

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result == "123-feature-branch"
        mock_manager.get_linked_branches.assert_called_once_with(123)
        # GraphQL should NOT be called (short-circuit)
        mock_graphql_query.assert_not_called()

    @pytest.mark.parametrize(
        "pr_state,is_draft,pr_number",
        [
            ("OPEN", True, 42),  # Draft PR
            ("OPEN", False, 43),  # Open (non-draft) PR
        ],
    )
    def test_no_linked_branch_single_pr_returns_branch(
        self,
        mock_manager: IssueBranchManager,
        pr_state: str,
        is_draft: bool,
        pr_number: int,
    ) -> None:
        """Test fallback: no linkedBranches, single draft/open PR found."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with single PR
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": pr_number,
                                        "state": pr_state,
                                        "isDraft": is_draft,
                                        "headRefName": "123-feature-branch",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result == "123-feature-branch"
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager._github_client._Github__requester.graphql_query.assert_called_once()  # type: ignore[attr-defined]

    def test_no_linked_branch_multiple_prs_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test multiple PRs found returns None with warning."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with TWO PRs
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 42,
                                        "state": "OPEN",
                                        "isDraft": True,
                                        "headRefName": "123-feature-branch-1",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 43,
                                        "state": "OPEN",
                                        "isDraft": False,
                                        "headRefName": "123-feature-branch-2",
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager._github_client._Github__requester.graphql_query.assert_called_once()  # type: ignore[attr-defined]

    def test_no_linked_branch_no_prs_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test no linkedBranches and no PRs returns None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with empty nodes
        timeline_response: dict[str, Any] = {
            "data": {"repository": {"issue": {"timelineItems": {"nodes": []}}}}
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager._github_client._Github__requester.graphql_query.assert_called_once()  # type: ignore[attr-defined]

    def test_invalid_issue_number_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test invalid issue numbers return None."""
        # Test with negative number
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=-1, repo_owner="test-owner", repo_name="test-repo"
        )
        assert result is None

        # Test with zero
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=0, repo_owner="test-owner", repo_name="test-repo"
        )
        assert result is None

    def test_graphql_error_returns_none(self, mock_manager: IssueBranchManager) -> None:
        """Test GraphQL errors handled by decorator return None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL to raise exception
        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            side_effect=GithubException(500, {"message": "Internal Server Error"}, None)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_repository_not_found_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test repository access failure returns None."""
        # Mock _get_repository to return None
        mock_manager._repository = None
        mock_manager._get_repository = Mock(return_value=None)  # type: ignore[method-assign]

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_malformed_timeline_response_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test malformed GraphQL timeline response returns None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL response with malformed data
        malformed_response: dict[str, Any] = {"data": None}  # Malformed response

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, malformed_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_issue_not_found_in_timeline_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test timeline query when issue is not found returns None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL response with null issue
        timeline_response: dict[str, Any] = {"data": {"repository": {"issue": None}}}

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=999, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_closed_prs_filtered_out(self, mock_manager: IssueBranchManager) -> None:
        """Test that closed PRs are filtered out and only OPEN PRs are considered."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with closed and open PRs
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 40,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-closed-pr",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 42,
                                        "state": "OPEN",
                                        "isDraft": True,
                                        "headRefName": "123-feature-branch",
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify - should return the OPEN PR branch, ignoring CLOSED
        assert result == "123-feature-branch"

    def test_non_pr_cross_references_filtered_out(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test that non-PR cross-references are filtered out."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with non-PR cross-reference
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        # This is an Issue, not a PR - missing PR-specific fields
                                        "number": 40,
                                        "title": "Related issue",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify - should return None as no valid PRs found
        assert result is None


class TestSearchBranchesByPattern:
    """Test suite for IssueBranchManager._search_branches_by_pattern()."""

    @pytest.fixture
    def mock_manager(self) -> IssueBranchManager:
        """Create a mock IssueBranchManager for testing."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        with (
            patch(
                "mcp_coder.utils.git_operations.is_git_repository", return_value=True
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_values",
                return_value={(("github", "token")): "fake_token"},
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            manager = IssueBranchManager(mock_path)
            return manager

    def test_search_branches_no_match(self, mock_manager: IssueBranchManager) -> None:
        """Empty refs list returns None."""
        mock_repo = Mock()
        # Both prefix pass and full scan return empty
        mock_repo.get_git_matching_refs.side_effect = [
            [],  # prefix pass
            [],  # full scan
        ]

        result = mock_manager._search_branches_by_pattern(252, mock_repo)

        assert result is None

    def test_search_branches_single_match_prefix(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Prefix pass finds '252-bar' — returns branch name without full scan."""
        mock_repo = Mock()
        # Prefix pass returns a matching ref
        mock_repo.get_git_matching_refs.return_value = [
            _make_git_ref("refs/heads/252-bar"),
        ]

        result = mock_manager._search_branches_by_pattern(252, mock_repo)

        assert result == "252-bar"
        # Should only call get_git_matching_refs once (prefix pass)
        mock_repo.get_git_matching_refs.assert_called_once_with("heads/252")

    def test_search_branches_single_match_nested(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Prefix pass empty, full scan finds 'feature/252-foo' — returns branch."""
        mock_repo = Mock()
        # Prefix pass returns no matches, full scan returns nested match
        mock_repo.get_git_matching_refs.side_effect = [
            [],  # prefix pass
            [_make_git_ref("refs/heads/feature/252-foo")],  # full scan
        ]

        result = mock_manager._search_branches_by_pattern(252, mock_repo)

        assert result == "feature/252-foo"
        assert mock_repo.get_git_matching_refs.call_count == 2

    def test_search_branches_multiple_matches(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Two matching refs in prefix pass returns None (ambiguous)."""
        mock_repo = Mock()
        mock_repo.get_git_matching_refs.return_value = [
            _make_git_ref("refs/heads/252-bar"),
            _make_git_ref("refs/heads/252-baz"),
        ]

        result = mock_manager._search_branches_by_pattern(252, mock_repo)

        assert result is None

    def test_search_branches_500_cap(self, mock_manager: IssueBranchManager) -> None:
        """501 refs in full scan — processes first 500, logs warning."""
        mock_repo = Mock()
        # Prefix pass: no matches
        # Full scan: 501 refs, none matching the pattern
        refs_501 = [_make_git_ref(f"refs/heads/other-branch-{i}") for i in range(501)]
        mock_repo.get_git_matching_refs.side_effect = [
            [],  # prefix pass
            refs_501,  # full scan
        ]

        with patch(
            "mcp_coder.utils.github_operations.issues.branch_manager.logger"
        ) as mock_logger:
            result = mock_manager._search_branches_by_pattern(252, mock_repo)

        assert result is None
        # Should log warning about exceeding 500 refs
        mock_logger.warning.assert_called()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "500" in warning_msg

    def test_search_branches_pattern_variations(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Matches expected patterns, does NOT match false positives."""
        mock_repo = Mock()

        # Test matching patterns individually via full scan
        # Test: "feature/252-foo" should match
        mock_repo.get_git_matching_refs.side_effect = [
            [],  # prefix pass
            [_make_git_ref("refs/heads/feature/252-foo")],  # full scan
        ]
        assert (
            mock_manager._search_branches_by_pattern(252, mock_repo)
            == "feature/252-foo"
        )

        # Test: "252-bar" should match (via prefix pass)
        mock_repo.get_git_matching_refs.side_effect = [
            [_make_git_ref("refs/heads/252-bar")],  # prefix pass
        ]
        assert mock_manager._search_branches_by_pattern(252, mock_repo) == "252-bar"

        # Test: "fix/252_baz" should match (underscore separator)
        mock_repo.get_git_matching_refs.side_effect = [
            [],  # prefix pass
            [_make_git_ref("refs/heads/fix/252_baz")],  # full scan
        ]
        assert mock_manager._search_branches_by_pattern(252, mock_repo) == "fix/252_baz"

        # Test: "1252-foo" should NOT match (different number)
        mock_repo.get_git_matching_refs.side_effect = [
            [_make_git_ref("refs/heads/1252-foo")],  # prefix pass
            [],  # full scan
        ]
        assert mock_manager._search_branches_by_pattern(252, mock_repo) is None

        # Test: "252" alone (no separator) should NOT match
        mock_repo.get_git_matching_refs.side_effect = [
            [_make_git_ref("refs/heads/252")],  # prefix pass
            [],  # full scan
        ]
        assert mock_manager._search_branches_by_pattern(252, mock_repo) is None
