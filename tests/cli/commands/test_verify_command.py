#!/usr/bin/env python3
"""Tests for the verify command module."""

import argparse
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import _LABEL_MAP, execute_verify


def _make_args(**kwargs: Any) -> argparse.Namespace:
    """Create a Namespace with defaults for execute_verify."""
    defaults: dict[str, Any] = {"check_models": False, "mcp_config": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestExecuteVerify:
    """Test the execute_verify function."""

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_execute_verify_returns_zero_on_success(
        self,
        mock_provider: MagicMock,
        mock_verify: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """Test that execute_verify returns 0 when overall_ok is True."""
        mock_provider.return_value = ("claude", "default")
        mock_verify.return_value = {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_works": {"ok": True, "value": "YES"},
            "api_integration": {"ok": True, "value": "OK", "error": None},
            "overall_ok": True,
        }
        mock_mlflow.return_value = {
            "installed": {"ok": False, "value": "not installed"},
            "overall_ok": True,
        }

        result = execute_verify(_make_args())

        assert result == 0
        mock_verify.assert_called_once()

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_execute_verify_returns_one_on_failure(
        self,
        mock_provider: MagicMock,
        mock_verify: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """Test that execute_verify returns 1 when overall_ok is False."""
        mock_provider.return_value = ("claude", "default")
        mock_verify.return_value = {
            "cli_found": {"ok": False, "value": "NO"},
            "cli_works": {"ok": False, "value": "NO"},
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        mock_mlflow.return_value = {
            "installed": {"ok": False, "value": "not installed"},
            "overall_ok": True,
        }

        result = execute_verify(_make_args())

        assert result == 1
        mock_verify.assert_called_once()

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_execute_verify_prints_status_lines(
        self,
        mock_provider: MagicMock,
        mock_verify: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that execute_verify prints formatted status lines."""
        mock_provider.return_value = ("claude", "default")
        mock_verify.return_value = {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_works": {"ok": True, "value": "YES"},
            "api_integration": {"ok": True, "value": "OK", "error": None},
            "overall_ok": True,
        }
        mock_mlflow.return_value = {
            "installed": {"ok": False, "value": "not installed"},
            "overall_ok": True,
        }

        execute_verify(_make_args())

        output = capsys.readouterr().out
        assert "=== BASIC VERIFICATION ===" in output
        # Check that status entries are printed (symbol is platform-dependent)
        assert "[OK]" in output or "\u2713" in output


class TestVerifyLabelMap:
    """Tests for label map coverage."""

    def test_mcp_adapter_labels_in_map(self) -> None:
        """Label map contains entries for MCP adapter checks."""
        assert "mcp_adapters" in _LABEL_MAP
        assert "langgraph" in _LABEL_MAP
        assert "mcp_agent_test" in _LABEL_MAP
