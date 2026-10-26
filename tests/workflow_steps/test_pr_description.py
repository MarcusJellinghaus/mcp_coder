"""Tests for mcp_coder.workflow_steps.pr_description."""

import pytest

from mcp_coder.workflow_steps.pr_description import closing_issue_numbers


class TestClosingIssueNumbers:
    """Test closing_issue_numbers function."""

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("Closes #3\nfixes #1, resolves: #3", [1, 3]),
            ("No reference", []),
            ("", []),
            ("#5", []),
        ],
    )
    def test_closing_issue_numbers(self, body: str, expected: list[int]) -> None:
        """Returns sorted, de-duplicated numbers of closed issues."""
        assert closing_issue_numbers(body) == expected
