"""Tests for the verify CLI orchestrator (Step 5)."""

import argparse
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (
    _compute_exit_code,
    _format_section,
    execute_verify,
)


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

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_all_sections_printed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """All three sections appear in output."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_ok()
        mock_ask_llm.return_value = "OK"

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "BASIC VERIFICATION" in output
        assert "LLM PROVIDER" in output
        assert "MLFLOW" in output

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_0_when_active_provider_works(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """Exit 0 when active provider (claude) succeeds."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        result = execute_verify(_make_args())

        assert result == 0

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_1_when_active_provider_fails(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """Exit 1 when active provider (langchain) fails."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_fail()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        result = execute_verify(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_1_when_mlflow_enabled_but_misconfigured(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """Exit 1 when MLflow is enabled and has errors."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_enabled_broken()
        mock_ask_llm.return_value = "OK"

        result = execute_verify(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_exit_0_when_mlflow_not_installed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """Exit 0 when MLflow not installed (informational)."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        result = execute_verify(_make_args())

        assert result == 0

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_claude_informational_when_langchain_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude CLI section is informational when provider=langchain (doesn't affect exit)."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_fail()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        # verify_langchain is NOT called because we mock _resolve_active_provider
        # but the code path calls it — we need to patch it too
        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args())

        # Claude failing should not cause exit 1 when langchain is active
        assert result == 0

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.resolve_mcp_config_path", return_value=None)
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_check_models_passed_to_langchain(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """--check-models flag forwarded to verify_langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        execute_verify(_make_args(check_models=True))

        mock_lc.assert_called_once_with(check_models=True, mcp_config_path=None)

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_langchain_not_called_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verify_langchain is not called when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            execute_verify(_make_args())
            mock_lc.assert_not_called()

        output = capsys.readouterr().out
        assert "uses Claude CLI" in output

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_test_prompt_displayed_in_output(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test prompt result line appears in LLM PROVIDER section."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "Test prompt" in output
        assert "responded OK" in output

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_test_prompt_failure_does_not_raise(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """execute_verify() continues when ask_llm raises."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.side_effect = Exception("timeout")

        result = execute_verify(_make_args())

        assert isinstance(result, int)

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_since_timestamp_passed_to_verify_mlflow(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
    ) -> None:
        """verify_mlflow() is called with a datetime since= argument."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        execute_verify(_make_args())

        call_kwargs = mock_mlflow.call_args
        assert call_kwargs.kwargs.get("since") is not None


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
        assert "Claude CLI Found     [OK] YES" in output

    def test_failed_entry_formatted_with_failure_symbol(self) -> None:
        """Entries with ok=False show [NO] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": False, "value": "NO"},
            "overall_ok": False,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert "Claude CLI Found     [NO] NO" in output

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


class TestVerifyUsesSharedResolveLlmMethod:
    """Tests that verify.py uses the shared resolve_llm_method()."""

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_verify_uses_llm_method_arg(
        self,
        mock_resolve: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--llm-method langchain is passed to resolve_llm_method and used."""
        mock_resolve.return_value = ("langchain", "cli argument")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args(llm_method="langchain"))

        mock_resolve.assert_called_once_with("langchain")
        assert result == 0
        output = capsys.readouterr().out
        assert "langchain" in output
        assert "cli argument" in output

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_verify_defaults_to_config(
        self,
        mock_resolve: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No --llm-method: resolve_llm_method returns config default_provider."""
        mock_resolve.return_value = ("langchain", "config default_provider")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        with patch("mcp_coder.cli.commands.verify.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args())

        mock_resolve.assert_called_once_with(None)
        assert result == 0
        output = capsys.readouterr().out
        assert "langchain" in output
        assert "config default_provider" in output

    @patch("mcp_coder.cli.commands.verify.ask_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_verify_defaults_to_claude(
        self,
        mock_resolve: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_ask_llm: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No arg, no config: resolve_llm_method returns claude default."""
        mock_resolve.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_ask_llm.return_value = "OK"

        result = execute_verify(_make_args())

        mock_resolve.assert_called_once_with(None)
        assert result == 0
        output = capsys.readouterr().out
        assert "claude" in output
        assert "default" in output


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
