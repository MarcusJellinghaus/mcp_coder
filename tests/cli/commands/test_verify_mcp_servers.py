"""Tests for MCP server health check integration in execute_verify."""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify

_LC_VERIFY = "mcp_coder.llm.providers.langchain.verification"
_VERIFY = "mcp_coder.cli.commands.verify"


def _make_args(**kwargs: Any) -> argparse.Namespace:
    """Create a Namespace with defaults for execute_verify."""
    defaults: dict[str, Any] = {
        "check_models": False,
        "mcp_config": None,
        "settings": None,
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
            "mcp-tools-py": {"ok": True, "value": "5 tools available", "tools": 5},
        },
        "overall_ok": True,
    }


class TestMcpServersInVerify:
    """Tests for MCP server health check integration in execute_verify."""

    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(
        f"{_VERIFY}.resolve_mcp_config_path",
        return_value="/fake/.mcp.json",
    )
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_servers_displayed_when_config_present(
        self,
        mock_provider: MagicMock,
        mock_find_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_prepare_env: MagicMock,
        _mock_claude_mcp: MagicMock,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """MCP SERVERS section shown when mcp_config is present."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_ok()

        execute_verify(_make_args(mcp_config=".mcp.json", project_dir=str(tmp_path)))
        output = capsys.readouterr().out

        assert "MCP SERVERS" in output
        assert "mcp-tools-py" in output
        assert "5 tools available" in output
        mock_mcp_servers.assert_called_once_with("/fake/.mcp.json", env_vars={"K": "V"})

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(
        f"{_VERIFY}.resolve_mcp_config_path",
        return_value=None,
    )
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_servers_skipped_when_no_config(
        self,
        mock_provider: MagicMock,
        mock_find_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """MCP SERVERS section hidden when no MCP config."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "MCP SERVERS" not in output
        mock_mcp_servers.assert_not_called()
