"""Tests for the verify CLI orchestrator (Step 5)."""

import argparse
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (  # pylint: disable=no-name-in-module
    _compute_exit_code,
    _format_section,
    _resolve_active_provider,
    execute_verify,
)


def _make_args(**kwargs: Any) -> argparse.Namespace:
    """Create a Namespace with defaults for execute_verify."""
    defaults = {"check_models": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _claude_ok() -> dict[str, Any]:
    return {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }


def _claude_fail() -> dict[str, Any]:
    return {
        "cli_found": {"ok": False, "value": "NO"},
        "cli_works": {"ok": False, "value": "NO"},
        "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
        "overall_ok": False,
    }


def _langchain_ok() -> dict[str, Any]:
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": True, "value": "sk-ab...7x2f", "source": "env var"},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": True, "value": "langchain-openai installed"},
        "test_prompt": {"ok": True, "value": "responded in 1.2s", "error": None},
        "overall_ok": True,
    }


def _langchain_fail() -> dict[str, Any]:
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": False, "value": None, "source": None},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": False, "value": "langchain-openai not installed"},
        "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
        "overall_ok": False,
    }


def _mlflow_ok() -> dict[str, Any]:
    return {
        "installed": {"ok": True, "value": "version 2.10.0"},
        "enabled": {"ok": True, "value": "(config.toml)"},
        "tracking_uri": {"ok": True, "value": "http://localhost:5000"},
        "connection": {"ok": True, "value": "tracking server reachable"},
        "experiment": {"ok": True, "value": '"default" (exists)'},
        "artifact_location": {"ok": True, "value": "not configured (using default)"},
        "overall_ok": True,
    }


def _mlflow_not_installed() -> dict[str, Any]:
    return {
        "installed": {"ok": False, "value": "not installed"},
        "overall_ok": True,
    }


def _mlflow_enabled_broken() -> dict[str, Any]:
    return {
        "installed": {"ok": True, "value": "version 2.10.0"},
        "enabled": {"ok": True, "value": "(config.toml)"},
        "tracking_uri": {"ok": False, "value": "http://bad:5000", "error": "invalid"},
        "connection": {"ok": False, "value": "unreachable: connection refused"},
        "experiment": {"ok": False, "value": '"default" (could not check)'},
        "artifact_location": {"ok": True, "value": "not configured (using default)"},
        "overall_ok": False,
    }


class TestVerifyOrchestration:
    """Tests for the verify CLI orchestrator."""

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_all_sections_printed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """All three sections appear in output."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_ok()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "BASIC VERIFICATION" in output
        assert "LLM PROVIDER" in output
        assert "MLFLOW" in output

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_exit_0_when_active_provider_works(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """Exit 0 when active provider (claude) succeeds."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()

        result = execute_verify(_make_args())

        assert result == 0

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_exit_1_when_active_provider_fails(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """Exit 1 when active provider (langchain) fails."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_fail()
        mock_mlflow.return_value = _mlflow_not_installed()

        result = execute_verify(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_exit_1_when_mlflow_enabled_but_misconfigured(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """Exit 1 when MLflow is enabled and has errors."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_enabled_broken()

        result = execute_verify(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_exit_0_when_mlflow_not_installed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """Exit 0 when MLflow not installed (informational)."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()

        result = execute_verify(_make_args())

        assert result == 0

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_claude_informational_when_langchain_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude CLI section is informational when provider=langchain (doesn't affect exit)."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_fail()
        mock_mlflow.return_value = _mlflow_not_installed()

        # verify_langchain is NOT called because we mock _resolve_active_provider
        # but the code path calls it — we need to patch it too
        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args())

        # Claude failing should not cause exit 1 when langchain is active
        assert result == 0

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_check_models_passed_to_langchain(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """--check-models flag forwarded to verify_langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()

        execute_verify(_make_args(check_models=True))

        mock_lc.assert_called_once_with(check_models=True)

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_langchain_not_called_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verify_langchain is not called when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()

        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            execute_verify(_make_args())
            mock_lc.assert_not_called()

        output = capsys.readouterr().out
        assert "uses Claude CLI" in output


class TestFormatSection:
    """Tests for _format_section output formatting (Decision 10)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[NO]", "warning": "[!!]"}

    def test_ok_entry_formatted_with_success_symbol(self) -> None:
        """Entries with ok=True show [OK] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": True, "value": "YES"},
            "overall_ok": True,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert "Claude CLI Found:   [OK] YES" in output

    def test_failed_entry_formatted_with_failure_symbol(self) -> None:
        """Entries with ok=False show [NO] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": False, "value": "NO"},
            "overall_ok": False,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert "Claude CLI Found:   [NO] NO" in output

    def test_skipped_entry_formatted(self) -> None:
        """Entries with ok=None show warning indicator."""
        result: dict[str, Any] = {
            "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
            "overall_ok": True,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[!!]" in output
        assert "skipped (no API key)" in output

    def test_error_shown_on_failure(self) -> None:
        """Error message appended when ok=False and error is present."""
        result: dict[str, Any] = {
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[NO] FAILED (not found)" in output

    def test_section_title_in_header(self) -> None:
        """Section header contains the title."""
        result: dict[str, Any] = {"overall_ok": True}
        output = _format_section("MY SECTION", result, self._symbols())
        assert "=== MY SECTION ===" in output


class TestResolveActiveProvider:
    """Tests for _resolve_active_provider helper."""

    @patch("mcp_coder.cli.commands.verify.get_config_values")
    def test_config_langchain(self, mock_config: MagicMock) -> None:
        """Provider from config.toml is returned."""
        mock_config.return_value = {("llm", "provider"): "langchain"}
        provider, source = _resolve_active_provider()
        assert provider == "langchain"
        assert source == "config.toml"

    @patch("mcp_coder.cli.commands.verify.get_config_values")
    @patch.dict(os.environ, {"MCP_CODER_LLM_PROVIDER": "langchain"})
    def test_env_var_override(self, mock_config: MagicMock) -> None:
        """Environment variable takes precedence over config."""
        mock_config.return_value = {("llm", "provider"): "claude"}
        provider, source = _resolve_active_provider()
        assert provider == "langchain"
        assert "env var" in source

    @patch("mcp_coder.cli.commands.verify.get_config_values")
    def test_default_is_claude(self, mock_config: MagicMock) -> None:
        """Default provider is claude when nothing configured."""
        mock_config.return_value = {("llm", "provider"): None}
        provider, source = _resolve_active_provider()
        assert provider == "claude"
        assert "default" in source

    @patch.dict(os.environ, {"MCP_CODER_LLM_PROVIDER": "ollama"})
    def test_unknown_provider_env_var_raises(self) -> None:
        """Unknown provider from env var raises ValueError."""
        with pytest.raises(ValueError, match="Unknown LLM provider 'ollama'"):
            _resolve_active_provider()

    @patch("mcp_coder.cli.commands.verify.get_config_values")
    def test_unknown_provider_config_raises(self, mock_config: MagicMock) -> None:
        """Unknown provider from config.toml raises ValueError."""
        mock_config.return_value = {("llm", "provider"): "ollama"}
        with pytest.raises(ValueError, match="Unknown LLM provider 'ollama'"):
            _resolve_active_provider()


class TestComputeExitCode:
    """Tests for _compute_exit_code logic."""

    def test_claude_active_ok(self) -> None:
        """Exit 0 when claude is active and ok."""
        assert (
            _compute_exit_code("claude", _claude_ok(), None, _mlflow_not_installed())
            == 0
        )

    def test_claude_active_fail(self) -> None:
        """Exit 1 when claude is active and fails."""
        assert (
            _compute_exit_code("claude", _claude_fail(), None, _mlflow_not_installed())
            == 1
        )

    def test_langchain_active_ok(self) -> None:
        """Exit 0 when langchain is active and ok."""
        assert (
            _compute_exit_code(
                "langchain", _claude_ok(), _langchain_ok(), _mlflow_not_installed()
            )
            == 0
        )

    def test_langchain_active_fail(self) -> None:
        """Exit 1 when langchain is active and fails."""
        assert (
            _compute_exit_code(
                "langchain", _claude_ok(), _langchain_fail(), _mlflow_not_installed()
            )
            == 1
        )

    def test_mlflow_enabled_broken(self) -> None:
        """Exit 1 when mlflow is enabled but broken."""
        assert (
            _compute_exit_code("claude", _claude_ok(), None, _mlflow_enabled_broken())
            == 1
        )

    def test_mlflow_not_installed_ok(self) -> None:
        """Exit 0 when mlflow not installed (informational)."""
        assert (
            _compute_exit_code("claude", _claude_ok(), None, _mlflow_not_installed())
            == 0
        )

    def test_mlflow_ok(self) -> None:
        """Exit 0 when mlflow is enabled and working."""
        assert _compute_exit_code("claude", _claude_ok(), None, _mlflow_ok()) == 0

    def test_langchain_none_fails(self) -> None:
        """Exit 1 when langchain is active but result is None."""
        assert (
            _compute_exit_code("langchain", _claude_ok(), None, _mlflow_not_installed())
            == 1
        )
