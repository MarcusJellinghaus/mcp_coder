"""Tests for the verify CLI orchestrator (Step 5 & 6)."""

import argparse
import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify


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
        "overall_ok": True,
    }


def _langchain_fail() -> dict[str, Any]:
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": False, "value": None, "source": None},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": False, "value": "langchain-openai not installed"},
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

    @patch("mcp_coder.cli.commands.verify.find_claude_executable", return_value=None)
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_all_sections_printed(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """LLM PROVIDER and MLFLOW sections appear; no BASIC VERIFICATION when langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_ok()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "BASIC VERIFICATION" not in output
        assert "LLM PROVIDER" in output
        assert "MLFLOW" in output

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_0_when_active_provider_works(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """Exit 0 when active provider (claude) succeeds."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 0

    @patch("mcp_coder.cli.commands.verify.find_claude_executable", return_value=None)
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_1_when_active_provider_fails(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
    ) -> None:
        """Exit 1 when active provider (langchain) fails."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_fail()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_1_when_mlflow_enabled_but_misconfigured(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """Exit 1 when MLflow is enabled and has errors."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_enabled_broken()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_0_when_mlflow_not_installed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """Exit 0 when MLflow not installed (informational)."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 0

    @patch("mcp_coder.cli.commands.verify.find_claude_executable")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_claude_informational_when_langchain_active(
        self,
        mock_provider: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude one-liner shown when langchain active and CLI found."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_find_claude.return_value = "/usr/bin/claude"
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args())

        assert result == 0
        output = capsys.readouterr().out
        assert "Claude CLI: available at /usr/bin/claude" in output
        assert "BASIC VERIFICATION" not in output

    @patch("mcp_coder.cli.commands.verify.find_claude_executable", return_value=None)
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_check_models_passed_to_langchain(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
    ) -> None:
        """--check-models flag forwarded to verify_langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args(check_models=True))

        mock_lc.assert_called_once_with(check_models=True, mcp_config_path=None)

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_langchain_not_called_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verify_langchain is not called when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            execute_verify(_make_args())
            mock_lc.assert_not_called()

        output = capsys.readouterr().out
        assert "uses Claude CLI" in output

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_test_prompt_displayed_in_output(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test prompt result line appears in LLM PROVIDER section."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "Test prompt" in output
        assert "responded OK" in output

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_test_prompt_failure_does_not_raise(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """execute_verify() continues when prompt_llm raises."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = Exception("timeout")

        result = execute_verify(_make_args())

        assert isinstance(result, int)

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_since_timestamp_passed_to_verify_mlflow(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """verify_mlflow() is called with since= (a UTC datetime)."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())

        mock_mlflow.assert_called_once()
        call_kwargs = mock_mlflow.call_args
        since_arg = call_kwargs.kwargs.get("since") or call_kwargs[1].get("since")
        assert isinstance(since_arg, datetime.datetime)
        assert since_arg.tzinfo is not None  # UTC-aware

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_log_to_mlflow_called_on_success(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """log_to_mlflow is called with the response when prompt succeeds."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        response = _minimal_llm_response()
        mock_prompt_llm.return_value = response

        execute_verify(_make_args())

        mock_log_mlflow.assert_called_once()
        call_args = mock_log_mlflow.call_args[0]
        assert call_args[0] == response  # response_data
        assert call_args[1] == "Reply with OK"  # prompt

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_log_to_mlflow_not_called_on_failure(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
    ) -> None:
        """log_to_mlflow is NOT called when prompt_llm raises."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = Exception("timeout")

        execute_verify(_make_args())

        mock_log_mlflow.assert_not_called()


class TestConditionalClaudeDisplay:
    """Tests for conditional Claude display based on active provider."""

    @patch("mcp_coder.cli.commands.verify.find_claude_executable")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_langchain_active_cli_found_shows_oneliner(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When langchain active and CLI binary exists, show brief one-liner."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_find_claude.return_value = "/usr/bin/claude"
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "Claude CLI: available at /usr/bin/claude (not active)" in output
        assert "BASIC VERIFICATION" not in output

    @patch("mcp_coder.cli.commands.verify.find_claude_executable")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_langchain_active_cli_not_found_skips_claude_section(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When langchain active and CLI not found, no BASIC VERIFICATION section."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_find_claude.return_value = None
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "BASIC VERIFICATION" not in output
        assert "Claude CLI:" not in output

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_claude_active_shows_full_section(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When claude active, show full BASIC VERIFICATION section as before."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "BASIC VERIFICATION" in output


class TestInstallSummaryBlock:
    """Tests for install summary block display."""

    @patch("mcp_coder.cli.commands.verify.find_claude_executable", return_value=None)
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_summary_block_shown_for_missing_packages(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When langchain packages missing, INSTALL INSTRUCTIONS block appears."""
        mock_provider.return_value = ("langchain", "config.toml")
        lc_result = _langchain_fail()
        lc_result["backend_package"] = {
            "ok": False,
            "value": "langchain-openai not installed",
            "install_hint": "pip install langchain-openai",
        }
        mock_lc.return_value = lc_result
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "INSTALL INSTRUCTIONS" in output
        assert "pip install langchain-openai" in output

    @patch("mcp_coder.cli.commands.verify.find_claude_executable", return_value=None)
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_no_summary_block_when_all_installed(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When all packages installed, no INSTALL INSTRUCTIONS block."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "INSTALL INSTRUCTIONS" not in output
