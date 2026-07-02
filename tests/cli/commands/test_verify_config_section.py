"""Tests for CONFIG section integration in execute_verify."""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify

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


def _claude_ok() -> dict[str, Any]:
    return {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }


def _mlflow_not_installed() -> dict[str, Any]:
    return {
        "installed": {"ok": False, "value": "not installed"},
        "overall_ok": True,
    }


def _config_ok() -> dict[str, Any]:
    """Return a verify_config result with no errors."""
    return {
        "entries": [
            {"label": "Config file", "status": "ok", "value": "/fake/config.toml"},
        ],
        "has_error": False,
    }


def _config_error() -> dict[str, Any]:
    """Return a verify_config result with invalid TOML error."""
    return {
        "entries": [
            {"label": "Config file", "status": "error", "value": "invalid TOML"},
            {"label": "Parse error", "status": "error", "value": "TOML parse error"},
        ],
        "has_error": True,
    }


def _config_warning() -> dict[str, Any]:
    """Return a verify_config result with missing file warning."""
    return {
        "entries": [
            {"label": "Config file", "status": "warning", "value": "not found"},
            {
                "label": "Expected path",
                "status": "info",
                "value": str(Path.home() / ".mcp_coder" / "config.toml"),
            },
            {
                "label": "Hint",
                "status": "info",
                "value": "Run 'mcp-coder init' to create a default config",
            },
        ],
        "has_error": False,
    }


class TestConfigSectionInVerify:
    """Tests for CONFIG section integration in execute_verify."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_config_section_displayed_first(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CONFIG section appears in output before BASIC VERIFICATION."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_verify_config.return_value = _config_ok()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        config_pos = output.index("CONFIG")
        basic_pos = output.index("BASIC VERIFICATION")
        assert config_pos < basic_pos

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_config_invalid_toml_causes_exit_1(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verify_config returning has_error=True causes exit code 1."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_verify_config.return_value = _config_error()

        exit_code = execute_verify(_make_args())

        assert exit_code == 1

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_config_missing_shows_warning(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Missing config shows warning symbol and 'not found' in output."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_verify_config.return_value = _config_warning()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "CONFIG" in output
        assert "not found" in output
