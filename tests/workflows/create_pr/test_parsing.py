"""Tests for create_PR workflow PR parsing functionality."""

import pytest

from mcp_coder.workflows.create_pr.core import parse_pr_summary


class TestParsePrSummary:
    """Test parse_pr_summary function."""

    def test_parse_structured_response(self) -> None:
        """Test parsing structured LLM response with TITLE: and BODY: markers."""
        response = """TITLE: feat: Add user authentication system
BODY:
## Summary
This PR implements a comprehensive authentication system.

## Changes
- JWT token management
- User registration and login
- Password reset functionality"""

        title, body = parse_pr_summary(response)

        assert title == "feat: Add user authentication system"
        assert "## Summary" in body
        assert "JWT token management" in body
        assert "Password reset functionality" in body

    def test_parse_simple_response(self) -> None:
        """Test parsing simple LLM response with title and body."""
        response = """feat: Add new user authentication system

This PR implements a comprehensive authentication system with:
- JWT token management
- User registration and login
- Password reset functionality

Closes #123"""

        title, body = parse_pr_summary(response)

        assert title == "feat: Add new user authentication system"
        assert "This PR implements a comprehensive authentication system" in body
        assert (
            "feat: Add new user authentication system" in body
        )  # First line included in body
        assert "Closes #123" in body

    def test_parse_conventional_commit_fallback(self) -> None:
        """Test parsing when structured format not found but conventional commit exists."""
        response = """Here's my analysis of the changes:

fix: Resolve database connection timeout issue

This change addresses the timeout problems we've been seeing."""

        title, body = parse_pr_summary(response)

        assert title == "fix: Resolve database connection timeout issue"
        assert "Here's my analysis of the changes:" in body

    def test_parse_single_line_response(self) -> None:
        """Test parsing single line response (title only)."""
        response = "fix: Resolve database connection timeout issue"

        title, body = parse_pr_summary(response)

        assert title == "fix: Resolve database connection timeout issue"
        assert (
            body == "fix: Resolve database connection timeout issue"
        )  # Fallback includes first line

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response."""
        response = ""

        title, body = parse_pr_summary(response)

        assert title == "Pull Request"
        assert body == "Pull Request"

    def test_parse_whitespace_only_response(self) -> None:
        """Test parsing response with only whitespace."""
        response = "   \n\n   \t   \n   "

        title, body = parse_pr_summary(response)

        assert title == "Pull Request"
        assert body == "Pull Request"

    def test_parse_multiline_with_empty_lines(self) -> None:
        """Test parsing response with empty lines."""
        response = """refactor: Improve code structure


This refactoring includes:

- Better separation of concerns
- Improved error handling


Tested with unit tests."""

        title, body = parse_pr_summary(response)

        assert title == "refactor: Improve code structure"
        assert "refactor: Improve code structure" in body
        assert "This refactoring includes" in body
        assert "Tested with unit tests." in body

    def test_parse_body_only_response(self) -> None:
        """Test parsing response with BODY: but no TITLE:."""
        response = """BODY:
## Summary
This implements new functionality.

## Changes
- Feature A
- Feature B"""

        title, body = parse_pr_summary(response)

        # Should find first non-empty line as title since no TITLE: marker
        assert "BODY:" in title or "## Summary" in title  # Fallback behavior
        assert "Feature A" in body

    def test_parse_title_only_response(self) -> None:
        """Test parsing response with TITLE: but no BODY:."""
        response = """TITLE: feat: Add amazing feature
Some additional context here."""

        title, body = parse_pr_summary(response)

        assert title == "feat: Add amazing feature"
        assert "Some additional context here." in body

    def test_parse_multiple_conventional_commits(self) -> None:
        """Test parsing when multiple conventional commit prefixes exist."""
        response = """I found several commits:
feat: Add authentication
fix: Resolve bug
docs: Update readme"""

        title, body = parse_pr_summary(response)

        # Should pick the first conventional commit as title
        assert title == "feat: Add authentication"
        assert "I found several commits:" in body
        assert "fix: Resolve bug" in body

    @pytest.mark.parametrize(
        "llm_response,expected_title,expected_body",
        [
            # Robot emoji footer
            (
                "TITLE: feat: add feature\nBODY:\n## Summary\nAdds feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)",
                "feat: add feature",
                "## Summary\nAdds feature",
            ),
            # Co-Authored-By footer
            (
                "TITLE: fix: bug fix\nBODY:\n## Summary\nFixes bug\n\nCo-authored-by: Claude Opus 4.5 <noreply@anthropic.com>",
                "fix: bug fix",
                "## Summary\nFixes bug",
            ),
            # Both footers
            (
                "TITLE: docs: update\nBODY:\n## Summary\nUpdates docs\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>",
                "docs: update",
                "## Summary\nUpdates docs",
            ),
            # Empty body
            ("TITLE: feat: test\nBODY:\n", "feat: test", ""),
        ],
    )
    def test_parse_pr_summary_strips_footers(
        self, llm_response: str, expected_title: str, expected_body: str
    ) -> None:
        """Test that parse_pr_summary() strips Claude footers from PR body."""
        title, body = parse_pr_summary(llm_response)

        assert title == expected_title
        assert body == expected_body

    def test_parse_pr_summary_preserves_footer_mentions_in_content(self) -> None:
        """Test that legitimate PR body content mentioning footers is preserved."""
        llm_response = (
            "TITLE: feat: add footer support\n"
            "BODY:\n"
            "## Summary\n"
            "This PR adds support for 🤖 robot emojis in content.\n"
            "The Co-Authored-By field is also documented."
        )

        title, body = parse_pr_summary(llm_response)

        assert title == "feat: add footer support"
        assert "## Summary" in body
        assert "🤖 robot emojis" in body
        assert "Co-Authored-By field" in body
