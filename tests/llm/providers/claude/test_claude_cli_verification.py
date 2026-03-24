#!/usr/bin/env python3
"""Tests for the verify_claude function."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_cli_verification import (
    verify_claude,
)


class TestVerifyClaude:
    """Test the verify_claude function."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    def test_returns_structured_dict(
        self,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test that verify_claude returns a structured dict."""
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/bin/claude",
            "version": "2.1.40",
            "works": True,
            "error": None,
        }
        mock_api_verify.return_value = (True, "/usr/bin/claude", None)

        result = verify_claude()

        assert result["cli_found"]["ok"] is True
        assert result["cli_found"]["value"] == "YES"
        assert "install_hint" not in result["cli_found"]
        assert result["cli_path"]["ok"] is True
        assert result["cli_path"]["value"] == "/usr/bin/claude"
        assert result["cli_version"]["ok"] is True
        assert result["cli_version"]["value"] == "2.1.40"
        assert result["cli_works"]["ok"] is True
        assert result["cli_works"]["value"] == "YES"
        assert result["api_integration"]["ok"] is True
        assert result["api_integration"]["value"] == "OK"
        assert result["api_integration"]["error"] is None
        assert result["overall_ok"] is True

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    def test_cli_not_found(
        self,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test when CLI is not found."""
        mock_basic_verify.return_value = {
            "found": False,
            "path": None,
            "version": None,
            "works": False,
            "error": "Claude CLI not found",
        }
        mock_api_verify.return_value = (False, None, "Claude CLI not accessible")

        result = verify_claude()

        assert result["cli_found"]["ok"] is False
        assert result["cli_found"]["value"] == "NO"
        assert (
            result["cli_found"]["install_hint"]
            == "https://docs.anthropic.com/en/docs/claude-code"
        )
        assert "cli_path" not in result
        assert "cli_version" not in result
        assert result["cli_works"]["ok"] is False
        assert result["api_integration"]["ok"] is False
        assert result["overall_ok"] is False

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    def test_cli_not_found_has_install_hint(
        self,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """When CLI is not found, cli_found entry includes install_hint with docs URL."""
        mock_basic_verify.return_value = {
            "found": False,
            "path": None,
            "version": None,
            "works": False,
            "error": "Claude CLI not found",
        }
        mock_api_verify.return_value = (False, None, "Claude CLI not accessible")

        result = verify_claude()

        assert "install_hint" in result["cli_found"]
        assert (
            result["cli_found"]["install_hint"]
            == "https://docs.anthropic.com/en/docs/claude-code"
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    def test_api_integration_fails(
        self,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test when basic verification succeeds but API integration fails."""
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": "1.0.0",
            "works": True,
            "error": None,
        }
        mock_api_verify.return_value = (False, None, "PATH configuration issue")

        result = verify_claude()

        assert result["cli_found"]["ok"] is True
        assert result["cli_works"]["ok"] is True
        assert result["api_integration"]["ok"] is False
        assert result["api_integration"]["value"] == "FAILED"
        assert result["api_integration"]["error"] == "PATH configuration issue"
        assert result["overall_ok"] is False

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    def test_api_integration_exception(
        self,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test when API verification throws an exception."""
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": "1.0.0",
            "works": True,
            "error": None,
        }
        mock_api_verify.side_effect = RuntimeError("Unexpected API error")

        result = verify_claude()

        assert result["api_integration"]["ok"] is False
        assert result["api_integration"]["value"] == "FAILED"
        assert "EXCEPTION" in result["api_integration"]["error"]
        assert result["overall_ok"] is False

    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation"
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use"
    )
    def test_partial_basic_verification_info(
        self,
        mock_api_verify: MagicMock,
        mock_basic_verify: MagicMock,
    ) -> None:
        """Test with partial basic verification information (found but doesn't work)."""
        mock_basic_verify.return_value = {
            "found": True,
            "path": "/usr/local/bin/claude",
            "version": None,
            "works": False,
            "error": "Permission denied",
        }
        mock_api_verify.return_value = (
            False,
            "/usr/local/bin/claude",
            "Cannot execute",
        )

        result = verify_claude()

        assert result["cli_found"]["ok"] is True
        assert result["cli_path"]["value"] == "/usr/local/bin/claude"
        assert "cli_version" not in result  # No version when None
        assert result["cli_works"]["ok"] is False
        assert result["overall_ok"] is False
