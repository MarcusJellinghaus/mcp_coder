"""Tests for shared issue helpers."""

import logging
from unittest.mock import Mock

import pytest

from mcp_coder.mcp_workspace_github import (
    BranchLookup,
    BranchLookupError,
    GithubException,
    GitHubRateLimitError,
)
from mcp_coder.workflow_utils.issue_helpers import (
    get_issue_status,
    is_marked,
    lookup_branch,
)
from tests.github_factories import make_issue_data

ISSUE_HELPERS = "mcp_coder.workflow_utils.issue_helpers"


class TestIssueStatus:
    """Test issue status extraction."""

    def test_get_issue_status_with_status_label(self) -> None:
        """Extracts status label from issue."""
        issue = make_issue_data(
            title="Test",
            labels=["bug", "status-07:code-review", "priority-high"],
            url="",
        )
        assert get_issue_status(issue) == "status-07:code-review"

    def test_get_issue_status_no_status_label(self) -> None:
        """Returns empty string if no status label."""
        issue = make_issue_data(
            title="Test",
            labels=["bug", "priority-high"],
            url="",
        )
        assert get_issue_status(issue) == ""


class TestIsMarked:
    """Test the first-line ❌ marker rule."""

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("", False),
            ("## ❌ Implementation Failed\ndetails", True),
            ("❌ handoff", True),
            ("Implementation Failed\n❌ details", False),
            ("\n## ❌ Implementation Failed", False),
            ("plain comment", False),
        ],
    )
    def test_is_marked(self, body: str, expected: bool) -> None:
        """Marker counts only when it appears on the first line."""
        assert is_marked(body) is expected


class TestLookupBranch:
    """Tests for lookup_branch()."""

    def test_found_returns_branch(self) -> None:
        cache = Mock()
        cache.lookup.return_value = BranchLookup("found", "12-fix")

        assert lookup_branch(cache, make_issue_data(number=12)) == "12-fix"

    @pytest.mark.parametrize(
        "result", [BranchLookup("not_found"), BranchLookup("ambiguous")]
    )
    def test_not_found_or_ambiguous_returns_none(self, result: BranchLookup) -> None:
        cache = Mock()
        cache.lookup.return_value = result

        assert lookup_branch(cache, make_issue_data(number=12)) is None

    @pytest.mark.parametrize(
        "exc",
        [
            BranchLookupError("graphql incomplete"),
            ValueError("bad"),
            GithubException(500, {"message": "server error"}),
        ],
    )
    def test_lookup_errors_return_none_with_warning(
        self, exc: Exception, caplog: pytest.LogCaptureFixture
    ) -> None:
        cache = Mock()
        cache.lookup.side_effect = exc

        with caplog.at_level(logging.WARNING, logger=ISSUE_HELPERS):
            assert lookup_branch(cache, make_issue_data(number=12)) is None

        assert any(
            r.levelno == logging.WARNING and "#12" in r.getMessage()
            for r in caplog.records
        )

    def test_rate_limit_propagates(self) -> None:
        cache = Mock()
        cache.lookup.side_effect = GitHubRateLimitError("limited")

        with pytest.raises(GitHubRateLimitError):
            lookup_branch(cache, make_issue_data(number=12))
