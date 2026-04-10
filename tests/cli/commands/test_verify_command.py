#!/usr/bin/env python3
"""Tests for the verify command module."""

import argparse
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import _LABEL_MAP, execute_verify
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus


def _make_args(**kwargs: Any) -> argparse.Namespace:
    """Create a Namespace with defaults for execute_verify."""
    defaults: dict[str, Any] = {
        "check_models": False,
        "mcp_config": None,
        "llm_method": None,
        "project_dir": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _minimal_llm_response() -> dict[str, Any]:
    """Return a minimal LLMResponseDict-shaped dict for mocking prompt_llm."""
    return {
        "version": "1.0",
        "timestamp": "2026-01-01T00:00:00",
        "text": "OK",
        "session_id": None,
        "provider": "claude",
        "raw_response": {},
    }


class TestExecuteVerify:
    """Test the execute_verify function."""

    @patch(
        "mcp_coder.cli.commands.verify.prompt_llm",
        return_value={
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        },
    )
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_execute_verify_returns_zero_on_success(
        self,
        mock_provider: MagicMock,
        mock_verify: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
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

    @patch(
        "mcp_coder.cli.commands.verify.prompt_llm",
        return_value={
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        },
    )
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_execute_verify_returns_one_on_failure(
        self,
        mock_provider: MagicMock,
        mock_verify: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
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

    @patch(
        "mcp_coder.cli.commands.verify.prompt_llm",
        return_value={
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        },
    )
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_execute_verify_prints_status_lines(
        self,
        mock_provider: MagicMock,
        mock_verify: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
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


_VERIFY = "mcp_coder.cli.commands.verify"
_LC_VERIFY = "mcp_coder.llm.providers.langchain.verification"


def _claude_ok() -> dict[str, Any]:
    return {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }


def _langchain_ok() -> dict[str, Any]:
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": True, "value": "sk-ab...7x2f", "source": "env var"},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": True, "value": "langchain-openai installed"},
        "overall_ok": True,
    }


def _mlflow_not_installed() -> dict[str, Any]:
    return {
        "installed": {"ok": False, "value": "not installed"},
        "overall_ok": True,
    }


def _mcp_ok() -> dict[str, Any]:
    return {
        "servers": {
            "tools-py": {"ok": True, "value": "5 tools available", "tools": 5},
        },
        "overall_ok": True,
    }


def _config_ok() -> dict[str, Any]:
    return {
        "entries": [
            {"label": "Config file", "status": "ok", "value": "/fake/config.toml"},
        ],
        "has_error": False,
    }


class TestProviderAwareMcpSections:
    """Integration tests for provider-aware MCP section ordering."""

    @patch(f"{_VERIFY}.verify_config", return_value=_config_ok())
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed())
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
    @patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_ok())
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok())
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default"))
    def test_claude_provider_shows_claude_mcp_section_first(
        self,
        _mock_provider: MagicMock,
        _mock_claude: MagicMock,
        _mock_resolve_mcp: MagicMock,
        _mock_mcp_servers: MagicMock,
        _mock_env: MagicMock,
        mock_parse: MagicMock,
        _mock_mlflow: MagicMock,
        _mock_prompt: MagicMock,
        _mock_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Any,
    ) -> None:
        """'via Claude Code' appears before 'via langchain-mcp-adapters'."""
        mock_parse.return_value = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        execute_verify(_make_args(project_dir=str(tmp_path)))
        output = capsys.readouterr().out
        claude_pos = output.index("via Claude Code")
        lc_pos = output.index("via langchain-mcp-adapters")
        assert claude_pos < lc_pos

    @patch(f"{_VERIFY}.verify_config", return_value=_config_ok())
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed())
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
    @patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_ok())
    @patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok())
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("langchain", "config.toml"))
    def test_langchain_provider_shows_langchain_section_first(
        self,
        _mock_provider: MagicMock,
        _mock_find: MagicMock,
        _mock_resolve_mcp: MagicMock,
        _mock_lc: MagicMock,
        _mock_mcp_servers: MagicMock,
        _mock_env: MagicMock,
        mock_parse: MagicMock,
        _mock_mlflow: MagicMock,
        _mock_prompt: MagicMock,
        _mock_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Any,
    ) -> None:
        """'via langchain-mcp-adapters' appears before 'via Claude Code'."""
        mock_parse.return_value = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        execute_verify(_make_args(project_dir=str(tmp_path)))
        output = capsys.readouterr().out
        lc_pos = output.index("via langchain-mcp-adapters")
        claude_pos = output.index("via Claude Code")
        assert lc_pos < claude_pos

    @patch(f"{_VERIFY}.verify_config", return_value=_config_ok())
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed())
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
    @patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_ok())
    @patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok())
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("langchain", "config.toml"))
    def test_claude_mcp_section_shows_for_completeness_when_langchain_active(
        self,
        _mock_provider: MagicMock,
        _mock_find: MagicMock,
        _mock_resolve_mcp: MagicMock,
        _mock_lc: MagicMock,
        _mock_mcp_servers: MagicMock,
        _mock_env: MagicMock,
        mock_parse: MagicMock,
        _mock_mlflow: MagicMock,
        _mock_prompt: MagicMock,
        _mock_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Any,
    ) -> None:
        """Claude MCP section shows 'for completeness' when langchain is active."""
        mock_parse.return_value = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        execute_verify(_make_args(project_dir=str(tmp_path)))
        output = capsys.readouterr().out
        # The Claude section should have "for completeness"
        assert "via Claude Code \u2014 for completeness" in output

    @patch(f"{_VERIFY}.verify_config", return_value=_config_ok())
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed())
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
    @patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_ok())
    @patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok())
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("langchain", "config.toml"))
    def test_claude_mcp_failure_when_not_active_does_not_exit_1(
        self,
        _mock_provider: MagicMock,
        _mock_find: MagicMock,
        _mock_resolve_mcp: MagicMock,
        _mock_lc: MagicMock,
        _mock_mcp_servers: MagicMock,
        _mock_env: MagicMock,
        mock_parse: MagicMock,
        _mock_mlflow: MagicMock,
        _mock_prompt: MagicMock,
        _mock_config: MagicMock,
        tmp_path: Any,
    ) -> None:
        """Exit code 0 when claude MCP fails but langchain is active."""
        mock_parse.return_value = [
            ClaudeMCPStatus(
                name="mcp-tools-py", status_text="Failed to start", ok=False
            ),
        ]
        exit_code = execute_verify(_make_args(project_dir=str(tmp_path)))
        assert exit_code == 0


class TestClaudeMcpParserFailedExitCode:
    """Test that execute_verify passes claude_mcp_ok=False when parser fails."""

    @patch(f"{_VERIFY}.verify_config", return_value=_config_ok())
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed())
    @patch(f"{_VERIFY}.parse_claude_mcp_list", return_value=None)
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
    @patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_ok())
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok())
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default"))
    def test_claude_active_mcp_parser_failed_exit_1(
        self,
        _mock_provider: MagicMock,
        _mock_claude: MagicMock,
        _mock_resolve_mcp: MagicMock,
        _mock_mcp_servers: MagicMock,
        _mock_env: MagicMock,
        _mock_parse: MagicMock,
        _mock_mlflow: MagicMock,
        _mock_prompt: MagicMock,
        _mock_config: MagicMock,
        tmp_path: Any,
    ) -> None:
        """Exit 1 when parse_claude_mcp_list returns None and claude is active."""
        exit_code = execute_verify(_make_args(project_dir=str(tmp_path)))
        assert exit_code == 1
