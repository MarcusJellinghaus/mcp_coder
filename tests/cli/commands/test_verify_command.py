#!/usr/bin/env python3
"""Tests for the verify command module."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify


class TestExecuteVerify:
    """Test the execute_verify function."""

    @patch("mcp_coder.cli.commands.verify._verify_claude_cli_installation")
    def test_execute_verify_calls_underlying_function(
        self, mock_verify: MagicMock
    ) -> None:
        """Test that execute_verify calls the underlying verification function."""
        mock_verify.return_value = 0  # Success
        args = argparse.Namespace()

        result = execute_verify(args)

        assert result == 0
        mock_verify.assert_called_once_with(args)

    @patch("mcp_coder.cli.commands.verify._verify_claude_cli_installation")
    def test_execute_verify_propagates_return_code(
        self, mock_verify: MagicMock
    ) -> None:
        """Test that execute_verify propagates the return code."""
        mock_verify.return_value = 1  # Error
        args = argparse.Namespace()

        result = execute_verify(args)

        assert result == 1
        mock_verify.assert_called_once_with(args)

    @patch("mcp_coder.cli.commands.verify._verify_claude_cli_installation")
    def test_execute_verify_passes_arguments_correctly(
        self, mock_verify: MagicMock
    ) -> None:
        """Test that execute_verify passes arguments correctly to the underlying function."""
        mock_verify.return_value = 0
        args = argparse.Namespace(some_option="test_value")

        result = execute_verify(args)

        mock_verify.assert_called_once_with(args)
        # Verify the args object is passed through unchanged
        call_args = mock_verify.call_args[0][0]
        assert call_args is args  # Should be the same object
