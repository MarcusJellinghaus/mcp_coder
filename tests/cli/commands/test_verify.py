#!/usr/bin/env python3
"""Tests for the verify CLI command integration."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.main import main


class TestVerifyCommandIntegration:
    """Test the verify command CLI integration."""

    @patch('mcp_coder.cli.main.verify_claude_cli_installation')
    @patch('sys.argv', ['mcp-coder', 'verify'])
    def test_verify_command_calls_verification_function(self, mock_verify: MagicMock) -> None:
        """Test that the verify CLI command calls the verification function."""
        mock_verify.return_value = 0  # Success
        
        result = main()
        
        assert result == 0
        mock_verify.assert_called_once()
        
        # Check that the function was called with proper arguments
        call_args = mock_verify.call_args[0][0]  # First positional argument (args)
        assert isinstance(call_args, argparse.Namespace)

    @patch('mcp_coder.cli.main.verify_claude_cli_installation')
    @patch('sys.argv', ['mcp-coder', 'verify'])
    def test_verify_command_propagates_return_code(self, mock_verify: MagicMock) -> None:
        """Test that the verify CLI command propagates the return code from verification."""
        mock_verify.return_value = 1  # Error
        
        result = main()
        
        assert result == 1
        mock_verify.assert_called_once()
