#!/usr/bin/env python3
"""Tests for the verify command."""

import argparse
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_cli_verification import (
    verify_claude_cli_installation,
)


class TestVerifyClaudeCliInstallation:
    """Test the verify_claude_cli_installation function."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    @patch("builtins.print")
    def test_successful_verification(
        self,
        mock_print: MagicMock,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test successful Claude verification."""
        # Setup successful verification results
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": "1.0.0",
            "works": True,
            "error": None,
        }
        mock_api_verify.return_value = (True, "/usr/local/bin/claude", None)

        args = argparse.Namespace()

        result = verify_claude_cli_installation(args)

        assert result == 0  # Success exit code

        # Check that verification functions were called
        mock_basic_verify.assert_called_once()
        mock_api_verify.assert_called_once()

        # Check that success messages were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        success_messages = [msg for msg in print_calls if "YES" in msg or "OK" in msg]
        assert len(success_messages) >= 2  # Should have multiple success indicators

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    @patch("builtins.print")
    def test_failed_basic_verification(
        self,
        mock_print: MagicMock,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test failed basic Claude verification."""
        # Setup failed verification results
        mock_basic_verify.return_value = {
            "found": False,
            "path": None,
            "version": None,
            "works": False,
            "error": "Claude CLI not found",
        }
        mock_api_verify.return_value = (False, None, "Claude CLI not accessible")

        args = argparse.Namespace()

        result = verify_claude_cli_installation(args)

        assert result == 1  # Error exit code

        # Check that failure messages were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        failure_messages = [
            msg
            for msg in print_calls
            if "NO" in msg or "FAILED" in msg or "Issues detected" in msg
        ]
        assert len(failure_messages) >= 2  # Should have multiple failure indicators

        # Check that recommendations were provided
        recommendation_messages = [msg for msg in print_calls if "npm install" in msg]
        assert len(recommendation_messages) >= 1

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    @patch("builtins.print")
    def test_basic_success_api_failure(
        self,
        mock_print: MagicMock,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test case where basic verification succeeds but API verification fails."""
        # Setup mixed verification results
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": "1.0.0",
            "works": True,
            "error": None,
        }
        mock_api_verify.return_value = (False, None, "PATH configuration issue")

        args = argparse.Namespace()

        result = verify_claude_cli_installation(args)

        assert result == 1  # Error exit code

        # Check that both success and failure messages were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        success_messages = [msg for msg in print_calls if "YES" in msg]
        failure_messages = [msg for msg in print_calls if "FAILED" in msg]

        assert len(success_messages) >= 2  # Basic verification successes
        assert len(failure_messages) >= 1  # API verification failure

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    @patch("builtins.print")
    def test_api_verification_exception(
        self,
        mock_print: MagicMock,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test case where API verification throws an exception."""
        # Setup basic verification success but API exception
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": "1.0.0",
            "works": True,
            "error": None,
        }
        mock_api_verify.side_effect = RuntimeError("Unexpected API error")

        args = argparse.Namespace()

        result = verify_claude_cli_installation(args)

        assert result == 1  # Error exit code

        # Check that exception was handled gracefully
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        exception_messages = [msg for msg in print_calls if "EXCEPTION" in msg]
        assert len(exception_messages) >= 1

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    @patch("builtins.print")
    def test_partial_basic_verification_info(
        self,
        mock_print: MagicMock,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test case with partial basic verification information."""
        # Setup verification with some missing info
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": None,  # Missing version
            "works": False,  # Doesn't work
            "error": "Permission denied",
        }
        mock_api_verify.return_value = (
            False,
            "/usr/local/bin/claude",
            "Cannot execute",
        )

        args = argparse.Namespace()

        result = verify_claude_cli_installation(args)

        assert result == 1  # Error exit code

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Should show path but not version
        path_messages = [msg for msg in print_calls if "/usr/local/bin/claude" in msg]
        assert len(path_messages) >= 1

        # Should show error information
        error_messages = [msg for msg in print_calls if "Permission denied" in msg]
        assert len(error_messages) >= 1


class TestVerifyCommandIntegration:
    """Integration tests for the verify command (require real Claude installation to be meaningful)."""

    @pytest.mark.claude_cli_integration
    def test_verify_command_structure(self) -> None:
        """Test that the verify command has the correct structure."""
        # This is a minimal test that doesn't require Claude to be installed
        # It just checks that the function can be called with proper arguments

        args = argparse.Namespace()

        # This should not crash, even if Claude is not installed
        # The actual return code depends on the environment
        result = verify_claude_cli_installation(args)

        # Should return either 0 (success) or 1 (failure), not crash
        assert result in [0, 1]
