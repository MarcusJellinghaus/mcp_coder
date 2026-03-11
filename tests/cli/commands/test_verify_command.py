#!/usr/bin/env python3
"""Tests for the verify command module."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify


class TestExecuteVerify:
    """Test the execute_verify function."""

    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._get_status_symbols")
    def test_execute_verify_returns_zero_on_success(
        self, mock_symbols: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test that execute_verify returns 0 when overall_ok is True."""
        mock_symbols.return_value = {
            "success": "[OK]",
            "failure": "[NO]",
            "warning": "[!!]",
        }
        mock_verify.return_value = {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_works": {"ok": True, "value": "YES"},
            "api_integration": {"ok": True, "value": "OK", "error": None},
            "overall_ok": True,
        }
        args = argparse.Namespace()

        result = execute_verify(args)

        assert result == 0
        mock_verify.assert_called_once()

    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._get_status_symbols")
    def test_execute_verify_returns_one_on_failure(
        self, mock_symbols: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test that execute_verify returns 1 when overall_ok is False."""
        mock_symbols.return_value = {
            "success": "[OK]",
            "failure": "[NO]",
            "warning": "[!!]",
        }
        mock_verify.return_value = {
            "cli_found": {"ok": False, "value": "NO"},
            "cli_works": {"ok": False, "value": "NO"},
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        args = argparse.Namespace()

        result = execute_verify(args)

        assert result == 1
        mock_verify.assert_called_once()

    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._get_status_symbols")
    @patch("builtins.print")
    def test_execute_verify_prints_status_lines(
        self, mock_print: MagicMock, mock_symbols: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test that execute_verify prints formatted status lines."""
        mock_symbols.return_value = {
            "success": "[OK]",
            "failure": "[NO]",
            "warning": "[!!]",
        }
        mock_verify.return_value = {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_works": {"ok": True, "value": "YES"},
            "api_integration": {"ok": True, "value": "OK", "error": None},
            "overall_ok": True,
        }
        args = argparse.Namespace()

        execute_verify(args)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "=== BASIC VERIFICATION ===" in print_calls
        # Check that status entries are printed
        status_lines = [msg for msg in print_calls if "[OK]" in msg]
        assert len(status_lines) >= 2
