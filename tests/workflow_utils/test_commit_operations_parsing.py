from mcp_coder.workflow_utils.commit_operations import (
    parse_llm_commit_response,
    strip_claude_footers,
)


class TestStripClaudeFooters:
    """Tests for strip_claude_footers function."""

    # Basic functionality tests
    def test_strip_no_footers_present(self) -> None:
        """Test message with no footers remains unchanged."""
        message = "feat: clean commit message"

        expected = "feat: clean commit message"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_robot_emoji_footer_only(self) -> None:
        """Test stripping message with only robot emoji footer."""
        message = """fix: bug fix

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""

        expected = "fix: bug fix"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_coauthored_footer_only(self) -> None:
        """Test stripping message with only Co-Authored footer."""
        message = """docs: update readme

Co-Authored-By: Claude <noreply@anthropic.com>"""

        expected = "docs: update readme"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_both_footers_present(self) -> None:
        """Test stripping message with both footers present."""
        message = """feat: add new feature

Some commit body text

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        expected = """feat: add new feature

Some commit body text"""

        result = strip_claude_footers(message)
        assert result == expected

    # Edge cases
    def test_strip_empty_message(self) -> None:
        """Test empty message remains unchanged."""
        message = ""

        expected = ""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_only_whitespace(self) -> None:
        """Test handling input with only whitespace."""
        message = "   \n\t  \n  "

        expected = ""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_whitespace_variations(self) -> None:
        """Test handling footers with various whitespace."""
        message = """feat: whitespace test

   🤖 Generated with [Claude Code](https://claude.com/claude-code)   

   Co-Authored-By: Claude <noreply@anthropic.com>   
   """

        expected = "feat: whitespace test"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_trailing_blank_lines(self) -> None:
        """Test stripping footers with trailing blank lines."""
        message = """feat: feature with trailing blanks



🤖 Generated with [Claude Code](https://claude.com/claude-code)


"""

        expected = "feat: feature with trailing blanks"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_mixed_with_blank_lines(self) -> None:
        """Test footers mixed with various blank lines."""
        message = """feat: mixed blank lines

Some body content


🤖 Generated with [Claude Code](https://claude.com/claude-code)


Co-Authored-By: Claude <noreply@anthropic.com>


"""

        expected = """feat: mixed blank lines

Some body content"""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_multiple_occurrences(self) -> None:
        """Test handling multiple occurrences of footer patterns."""
        message = """feat: multiple footers

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Some content here
Co-Authored-By: Claude <noreply@anthropic.com>
More content
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        # Only removes footers from the end, preserves content in middle
        expected = """feat: multiple footers

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Some content here
Co-Authored-By: Claude <noreply@anthropic.com>
More content"""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_case_sensitive(self) -> None:
        """Test that footer matching is case sensitive."""
        message = """feat: case test

co-authored-by: claude <noreply@anthropic.com>
🤖 generated with [claude code](https://claude.com/claude-code)"""

        # Robot emoji line is removed (starts with 🤖), but co-authored line remains (wrong case)
        expected = """feat: case test

co-authored-by: claude <noreply@anthropic.com>"""

        result = strip_claude_footers(message)
        assert result == expected

    # Content preservation tests
    def test_preserve_legitimate_content(self) -> None:
        """Test preservation of legitimate content that mentions footers."""
        message = """feat: add 🤖 emoji support

This commit adds robot emoji support.
The Co-Authored-By feature is also mentioned.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""

        expected = """feat: add 🤖 emoji support

This commit adds robot emoji support.
The Co-Authored-By feature is also mentioned."""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_preserve_multiline_body(self) -> None:
        """Test preservation of multi-line body content."""
        message = """feat: complex commit

This is the first paragraph of the body.

This is the second paragraph with more details.
It spans multiple lines and should be preserved.

And a third paragraph here.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        expected = """feat: complex commit

This is the first paragraph of the body.

This is the second paragraph with more details.
It spans multiple lines and should be preserved.

And a third paragraph here."""

        result = strip_claude_footers(message)
        assert result == expected

    def test_parse_llm_commit_response_multi_line(self) -> None:
        """Test parsing multi-line LLM response."""
        response = """feat: add new feature

This adds a new authentication feature
with proper error handling."""

        summary, body = parse_llm_commit_response(response)

        assert (
            summary
            == "feat: add new feature\n\nThis adds a new authentication feature\nwith proper error handling."
        )
        assert (
            body
            == "This adds a new authentication feature\nwith proper error handling."
        )

    def test_parse_llm_commit_response_multi_line_with_extra_spacing(self) -> None:
        """Test parsing multi-line LLM response with extra spacing."""
        response = """   feat: add new feature   

   This adds a new authentication feature   
   with proper error handling.   
   
   Additional details here.   """

        summary, body = parse_llm_commit_response(response)

        expected_summary = "feat: add new feature\n\nThis adds a new authentication feature\nwith proper error handling.\n\nAdditional details here."
        expected_body = "This adds a new authentication feature\nwith proper error handling.\n\nAdditional details here."

        assert summary == expected_summary
        assert body == expected_body

    def test_parse_llm_commit_response_empty(self) -> None:
        """Test parsing empty LLM response."""
        response = ""

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_none(self) -> None:
        """Test parsing None LLM response."""
        response = None

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_whitespace_only(self) -> None:
        """Test parsing whitespace-only LLM response."""
        response = "   \n  \t  \n  "

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_single_line_with_whitespace(self) -> None:
        """Test parsing single line with surrounding whitespace."""
        response = "   feat: add new feature   "

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None

    def test_parse_llm_commit_response_empty_lines_between_content(self) -> None:
        """Test parsing response with empty lines between content."""
        response = """feat: add new feature


This is the body content


More body content here"""

        summary, body = parse_llm_commit_response(response)

        expected_summary = "feat: add new feature\n\nThis is the body content\n\nMore body content here"
        expected_body = "This is the body content\n\nMore body content here"

        assert summary == expected_summary
        assert body == expected_body

    def test_parse_llm_commit_response_only_empty_lines_after_summary(self) -> None:
        """Test parsing response with only empty lines after summary."""
        response = """feat: add new feature




"""

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None


class TestParseLLMCommitResponse:
    """Tests for parse_llm_commit_response function."""

    def test_parse_llm_commit_response_single_line(self) -> None:
        """Test parsing single line LLM response."""
        response = "feat: add new feature"

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None

    def test_parse_llm_commit_response_multi_line(self) -> None:
        """Test parsing multi-line LLM response."""
        response = """feat: add new feature

This adds a new authentication feature
with proper error handling."""

        summary, body = parse_llm_commit_response(response)

        assert (
            summary
            == "feat: add new feature\n\nThis adds a new authentication feature\nwith proper error handling."
        )
        assert (
            body
            == "This adds a new authentication feature\nwith proper error handling."
        )

    def test_parse_llm_commit_response_empty(self) -> None:
        """Test parsing empty LLM response."""
        response = ""

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_whitespace_only(self) -> None:
        """Test parsing whitespace-only LLM response."""
        response = "   \n  \t  \n  "

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None
