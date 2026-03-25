"""Tests that verify.py uses the shared resolve_llm_method()."""

import argparse
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


class TestVerifyUsesSharedResolveLlmMethod:
    """Tests that verify.py uses the shared resolve_llm_method()."""

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_verify_uses_llm_method_arg(
        self,
        mock_resolve: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--llm-method langchain is passed to resolve_llm_method and used."""
        mock_verify_config.return_value = {
            "entries": [{"label": "Config file", "status": "ok", "value": "ok"}],
            "has_error": False,
        }
        mock_resolve.return_value = ("langchain", "cli argument")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_LC_VERIFY}.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args(llm_method="langchain"))

        mock_resolve.assert_called_once_with("langchain")
        assert result == 0
        output = capsys.readouterr().out
        assert "langchain" in output
        assert "cli argument" in output

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_verify_defaults_to_config(
        self,
        mock_resolve: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No --llm-method: resolve_llm_method returns config default_provider."""
        mock_verify_config.return_value = {
            "entries": [{"label": "Config file", "status": "ok", "value": "ok"}],
            "has_error": False,
        }
        mock_resolve.return_value = ("langchain", "config default_provider")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_LC_VERIFY}.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args())

        mock_resolve.assert_called_once_with(None)
        assert result == 0
        output = capsys.readouterr().out
        assert "langchain" in output
        assert "config default_provider" in output

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_verify_defaults_to_claude(
        self,
        mock_resolve: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No arg, no config: resolve_llm_method returns claude default."""
        mock_verify_config.return_value = {
            "entries": [{"label": "Config file", "status": "ok", "value": "ok"}],
            "has_error": False,
        }
        mock_resolve.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        mock_resolve.assert_called_once_with(None)
        assert result == 0
        output = capsys.readouterr().out
        assert "claude" in output
        assert "default" in output
