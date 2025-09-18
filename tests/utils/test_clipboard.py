"""Tests for clipboard utilities."""

from unittest.mock import patch

import pyperclip
import pytest

from mcp_coder.utils.clipboard import (
    get_clipboard_text,
    parse_commit_message,
    validate_commit_message,
)


class TestGetClipboardText:
    """Tests for get_clipboard_text function."""

    @patch("mcp_coder.utils.clipboard.pyperclip.paste")
    def test_get_clipboard_text_success(self, mock_paste):
        """Test successful clipboard text retrieval."""
        # Setup mock
        mock_paste.return_value = "test commit message"

        # Execute
        success, text, error = get_clipboard_text()

        # Verify
        assert success is True
        assert text == "test commit message"
        assert error is None
        mock_paste.assert_called_once()

    @patch("mcp_coder.utils.clipboard.pyperclip.paste")
    def test_get_clipboard_text_empty(self, mock_paste):
        """Test handling of empty clipboard."""
        # Setup mock
        mock_paste.return_value = "   "  # Only whitespace

        # Execute
        success, text, error = get_clipboard_text()

        # Verify
        assert success is False
        assert text == ""
        assert error == "Clipboard is empty"
        mock_paste.assert_called_once()

    @patch("mcp_coder.utils.clipboard.pyperclip.paste")
    def test_get_clipboard_text_none_result(self, mock_paste):
        """Test handling when paste returns None."""
        # Setup mock
        mock_paste.return_value = None

        # Execute
        success, text, error = get_clipboard_text()

        # Verify
        assert success is False
        assert text == ""
        assert error == "Clipboard is empty"
        mock_paste.assert_called_once()

    @patch("mcp_coder.utils.clipboard.pyperclip.paste")
    def test_get_clipboard_text_pyperclip_exception(self, mock_paste):
        """Test handling of pyperclip exceptions."""
        # Setup mock
        mock_paste.side_effect = pyperclip.PyperclipException(
            "No clipboard mechanism found"
        )

        # Execute
        success, text, error = get_clipboard_text()

        # Verify
        assert success is False
        assert text == ""
        assert error == "Clipboard access failed: No clipboard mechanism found"
        mock_paste.assert_called_once()

    @patch("mcp_coder.utils.clipboard.pyperclip.paste")
    def test_get_clipboard_text_unexpected_error(self, mock_paste):
        """Test handling of unexpected errors."""
        # Setup mock
        mock_paste.side_effect = RuntimeError("unexpected error")

        # Execute
        success, text, error = get_clipboard_text()

        # Verify
        assert success is False
        assert text == ""
        assert error == "Clipboard access failed: unexpected error"
        mock_paste.assert_called_once()


class TestValidateCommitMessage:
    """Tests for validate_commit_message function."""

    def test_validate_commit_message_empty(self):
        """Test validation of empty commit message."""
        # Empty string
        valid, error = validate_commit_message("")
        assert valid is False
        assert error == "Commit message cannot be empty"

        # Only whitespace
        valid, error = validate_commit_message("   \n  \t  ")
        assert valid is False
        assert error == "Commit message cannot be empty"

    def test_validate_commit_message_single_line_valid(self):
        """Test validation of valid single line commit messages."""
        test_cases = [
            "fix: resolve authentication bug",
            "feat: add user registration",
            "docs: update README with new examples",
            "refactor: simplify error handling logic",
        ]

        for message in test_cases:
            valid, error = validate_commit_message(message)
            assert valid is True, f"Failed for message: {message}"
            assert error is None

    def test_validate_commit_message_single_line_long(self):
        """Test validation of long single line commit message."""
        # Create a message longer than 72 characters
        long_message = "fix: " + "a" * 70  # 74 characters total

        with patch("mcp_coder.utils.clipboard.logger") as mock_logger:
            valid, error = validate_commit_message(long_message)

            assert valid is True  # Still valid, just warns
            assert error is None
            mock_logger.warning.assert_called_once()

    def test_validate_commit_message_multi_line_valid(self):
        """Test validation of valid multi-line commit messages."""
        message = """feat: add user registration

Implements user signup with email validation and password requirements.
Includes form validation and database integration."""

        valid, error = validate_commit_message(message)
        assert valid is True
        assert error is None

    def test_validate_commit_message_multi_line_invalid(self):
        """Test validation of invalid multi-line commit messages."""
        message = """feat: add user registration
Implements user signup with email validation.
More details here."""

        valid, error = validate_commit_message(message)
        assert valid is False
        assert error == "Multi-line commit message must have empty second line"

    def test_validate_commit_message_empty_first_line(self):
        """Test validation with empty first line."""
        message = "\nSome body text"

        valid, error = validate_commit_message(message)
        assert valid is False
        assert error == "Commit message cannot be empty"

    def test_validate_commit_message_only_empty_lines(self):
        """Test validation with only empty lines."""
        message = "\n\n\n"

        valid, error = validate_commit_message(message)
        assert valid is False
        assert error == "Commit message cannot be empty"


class TestParseCommitMessage:
    """Tests for parse_commit_message function."""

    def test_parse_commit_message_empty(self):
        """Test parsing empty commit message."""
        summary, body = parse_commit_message("")
        assert summary == ""
        assert body is None

    def test_parse_commit_message_single_line(self):
        """Test parsing single line commit message."""
        message = "fix: resolve authentication bug"
        summary, body = parse_commit_message(message)

        assert summary == "fix: resolve authentication bug"
        assert body is None

    def test_parse_commit_message_single_line_with_whitespace(self):
        """Test parsing single line with whitespace."""
        message = "  fix: resolve authentication bug  "
        summary, body = parse_commit_message(message)

        assert summary == "fix: resolve authentication bug"
        assert body is None

    def test_parse_commit_message_multi_line_valid(self):
        """Test parsing valid multi-line commit message."""
        message = """feat: add user registration

Implements user signup with email validation and password requirements.
Includes form validation and database integration.
Also adds unit tests for the new functionality."""

        summary, body = parse_commit_message(message)

        assert summary == "feat: add user registration"
        expected_body = """Implements user signup with email validation and password requirements.
Includes form validation and database integration.
Also adds unit tests for the new functionality."""
        assert body == expected_body

    def test_parse_commit_message_multi_line_with_trailing_empty_lines(self):
        """Test parsing multi-line message with trailing empty lines."""
        message = """feat: add user registration

Implements user signup functionality.

"""

        summary, body = parse_commit_message(message)

        assert summary == "feat: add user registration"
        assert body == "Implements user signup functionality."

    def test_parse_commit_message_multi_line_invalid_format(self):
        """Test parsing multi-line message with invalid format (no empty second line)."""
        message = """feat: add user registration
Implements user signup functionality.
More details here."""

        summary, body = parse_commit_message(message)

        assert summary == "feat: add user registration"
        assert body is None  # No valid body due to invalid format

    def test_parse_commit_message_only_summary_and_empty_line(self):
        """Test parsing message with only summary and empty line."""
        message = """fix: resolve bug

"""

        summary, body = parse_commit_message(message)

        assert summary == "fix: resolve bug"
        assert body is None

    def test_parse_commit_message_preserves_body_formatting(self):
        """Test that body formatting is preserved."""
        message = """feat: add configuration system

This adds a new configuration system with the following features:
- YAML-based configuration files
- Environment variable overrides
- Validation and type checking

Example usage:
    config = load_config('app.yaml')
    db_url = config.database.url"""

        summary, body = parse_commit_message(message)

        assert summary == "feat: add configuration system"
        expected_body = """This adds a new configuration system with the following features:
- YAML-based configuration files
- Environment variable overrides
- Validation and type checking

Example usage:
    config = load_config('app.yaml')
    db_url = config.database.url"""
        assert body == expected_body
