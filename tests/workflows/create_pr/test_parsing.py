"""Tests for create_PR workflow PR parsing functionality."""

import logging

import pytest

from mcp_coder.workflows.create_pr.core import (
    ensure_closing_reference,
    parse_pr_summary,
)


class TestEnsureClosingReference:
    """Test ensure_closing_reference function."""

    @pytest.mark.parametrize(
        "body",
        [
            "Closes #123",
            "fixes #123",
            "RESOLVED #123",
            "close #123",
            "Fix #123",
            "resolve #123",
            "text\n\nCloses  #123.",
            "Closes: #123",
            "Fixes:#123",
        ],
    )
    def test_detects_existing_reference(self, body: str) -> None:
        """Body already closing the issue is returned unchanged."""
        assert ensure_closing_reference(body, 123) == body

    @pytest.mark.parametrize(
        "body",
        [
            "No reference",
            "Closes #1234",
            "prefixes #123",
            "See #123",
        ],
    )
    def test_appends_when_missing(self, body: str) -> None:
        """Closing reference is appended when the body lacks one."""
        assert ensure_closing_reference(body, 123) == body + "\n\nCloses #123"

    def test_other_issue_appends_and_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Body closing other issues gets the reference and one warning."""
        with caplog.at_level(logging.WARNING):
            result = ensure_closing_reference("Closes #7\nFixes #9\nCloses #7", 123)

        assert result.endswith("\n\nCloses #123")
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        message = warnings[0].getMessage()
        assert "7" in message
        assert "9" in message


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
