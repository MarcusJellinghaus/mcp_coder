"""Tests for LLM response processing utilities."""

import pytest

from mcp_coder.workflow_utils.llm_response_utils import (
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

    def test_strip_footers_case_insensitive(self) -> None:
        """Test that footer matching is case insensitive."""
        message = """feat: case test

co-authored-by: claude <noreply@anthropic.com>
🤖 generated with [claude code](https://claude.com/claude-code)"""

        # Both footers are removed regardless of case (robot emoji and lowercase co-authored)
        expected = "feat: case test"

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

    # New parameterized tests for case-insensitive matching and model variations
    @pytest.mark.parametrize(
        "message,expected",
        [
            # Case-insensitive variations
            (
                "feat: add feature\n\nCo-authored-by: Claude Opus 4.5 <noreply@anthropic.com>",
                "feat: add feature",
            ),
            (
                "feat: add feature\n\nco-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>",
                "feat: add feature",
            ),
            (
                "feat: add feature\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>",
                "feat: add feature",
            ),
        ],
    )
    def test_strip_coauthored_case_insensitive(
        self, message: str, expected: str
    ) -> None:
        """Test case-insensitive matching for Co-Authored-By patterns."""
        result = strip_claude_footers(message)
        assert result == expected

    @pytest.mark.parametrize(
        "message,expected",
        [
            # Model name variations
            (
                "feat: test\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>",
                "feat: test",
            ),
            (
                "feat: test\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>",
                "feat: test",
            ),
            (
                "feat: test\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                "feat: test",
            ),
        ],
    )
    def test_strip_coauthored_model_variations(
        self, message: str, expected: str
    ) -> None:
        """Test stripping Co-Authored-By with different Claude model names."""
        result = strip_claude_footers(message)
        assert result == expected

    def test_preserve_autorunner_bot_footer(self) -> None:
        """Test that AutoRunner Bot footers are preserved (not removed)."""
        message = """feat: add feature

Co-Authored-By: AutoRunner Bot <autorunner@example.com>"""

        expected = """feat: add feature

Co-Authored-By: AutoRunner Bot <autorunner@example.com>"""

        result = strip_claude_footers(message)
        assert result == expected
