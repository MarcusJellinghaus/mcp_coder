"""Tests for the verify CLI orchestrator (Step 5 & 6)."""

import argparse
import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import _format_mcp_section, execute_verify

# Patch target for lazily-imported langchain verification functions
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

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_all_sections_printed(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_exit_0_when_active_provider_works(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """Exit 0 when active provider (claude) succeeds."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 0

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_exit_1_when_active_provider_fails(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
    ) -> None:
        """Exit 1 when active provider (langchain) fails."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_fail()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 1

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_exit_1_when_mlflow_enabled_but_misconfigured(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """Exit 1 when MLflow is enabled and has errors."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_enabled_broken()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 1

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_exit_0_when_mlflow_not_installed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """Exit 0 when MLflow not installed (informational)."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 0

    @patch(f"{_VERIFY}.find_claude_executable")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_claude_informational_when_langchain_active(
        self,
        mock_provider: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude one-liner shown when langchain active and CLI found."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_find_claude.return_value = "/usr/bin/claude"
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_LC_VERIFY}.verify_langchain") as mock_lc:
            mock_lc.return_value = _langchain_ok()
            result = execute_verify(_make_args())

        assert result == 0
        output = capsys.readouterr().out
        assert "Claude CLI: available at /usr/bin/claude" in output
        assert "BASIC VERIFICATION" not in output

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_check_models_passed_to_langchain(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
    ) -> None:
        """--check-models flag forwarded to verify_langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args(check_models=True))

        mock_lc.assert_called_once_with(check_models=True, mcp_config_path=None)

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_langchain_not_called_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verify_langchain is not called when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_LC_VERIFY}.verify_langchain") as mock_lc:
            execute_verify(_make_args())
            mock_lc.assert_not_called()

        output = capsys.readouterr().out
        assert "uses Claude CLI" in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_test_prompt_displayed_in_output(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_test_prompt_failure_does_not_raise(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """execute_verify() continues when prompt_llm raises."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = Exception("timeout")

        result = execute_verify(_make_args())

        assert isinstance(result, int)

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_since_timestamp_passed_to_verify_mlflow(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(
        f"{_VERIFY}.resolve_mcp_config_path",
        return_value="/fake/.mcp.json",
    )
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_prompt_llm_receives_mcp_config_and_execution_dir(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """prompt_llm is called with mcp_config and execution_dir kwargs."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = {
            "servers": {"tools-py": {"ok": True, "value": "5 tools", "tools": 5}},
            "overall_ok": True,
        }
        mock_verify_config.return_value = {
            "entries": [],
            "has_error": False,
        }

        execute_verify(_make_args(mcp_config=".mcp.json", project_dir=str(tmp_path)))

        # Find the test prompt call ("Reply with OK")
        test_prompt_calls = [
            c for c in mock_prompt_llm.call_args_list if c[0][0] == "Reply with OK"
        ]
        assert len(test_prompt_calls) == 1
        call_kwargs = test_prompt_calls[0][1]
        assert call_kwargs["mcp_config"] == "/fake/.mcp.json"
        assert "execution_dir" in call_kwargs

    @patch(
        f"{_VERIFY}._run_mcp_edit_smoke_test",
        return_value="  MCP edit smoke test  [OK]",
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_list_mcp_tools_flag_passed_to_format(
        self,
        mock_provider: MagicMock,
        mock_find_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_smoke_test: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--list-mcp-tools flag flows from args to _format_mcp_section."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_ok()

        with patch(f"{_VERIFY}._format_mcp_section") as mock_fmt:
            mock_fmt.return_value = "mocked"
            execute_verify(_make_args(list_mcp_tools=True, mcp_config=".mcp.json"))
            mock_fmt.assert_called_once()
            call_kwargs = mock_fmt.call_args
            assert call_kwargs.kwargs.get("list_mcp_tools") is True


class TestVerifyTestPromptFailure:
    """Tests for improved test prompt failure output (Step 5A)."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_connection_error_shows_category(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """ConnectionResetError shows classified category, not raw traceback."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = ConnectionResetError("Connection reset by peer")

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "FAILED" in output
        assert "connection-reset" in output
        # Should NOT contain the raw exception message
        assert "Connection reset by peer" not in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_non_connection_error_shows_type_and_message(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Non-connection errors show type(exc).__name__: str(exc) directly."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = RuntimeError("oops")

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "FAILED" in output
        assert "RuntimeError: oops" in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_failure_shows_debug_hint(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Failure output includes --debug hint."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = RuntimeError("fail")

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "Run with --debug for detailed diagnostics." in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_oserror_shows_category(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """OSError with WinError 10054 uses classify_connection_error."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        exc = OSError(10054, "An existing connection was forcibly closed")
        mock_prompt_llm.side_effect = exc

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "FAILED" in output
        assert "connection-reset" in output


class TestConditionalClaudeDisplay:
    """Tests for conditional Claude display based on active provider."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.find_claude_executable")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_langchain_active_cli_found_shows_oneliner(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @patch(f"{_VERIFY}.find_claude_executable")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_langchain_active_cli_not_found_skips_claude_section(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_claude_active_shows_full_section(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_summary_block_shown_for_missing_packages(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_no_summary_block_when_all_installed(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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


def _mcp_servers_ok() -> dict[str, Any]:
    """Return an MCP server health check result with overall_ok=True."""
    return {
        "servers": {
            "tools-py": {
                "ok": True,
                "value": "3 tools",
                "tool_names": [
                    ("read_file", "Read file contents"),
                    ("save_file", "Write content to a file"),
                    ("edit_file", "Edit a file"),
                ],
            }
        },
        "overall_ok": True,
    }


def _mcp_servers_fail() -> dict[str, Any]:
    """Return an MCP server health check result with overall_ok=False."""
    return {
        "servers": {
            "tools-py": {
                "ok": False,
                "value": "connection refused",
            }
        },
        "overall_ok": False,
    }


class TestVerifyMcpAllProviders:
    """Tests for provider-independent MCP verification + ImportError handling."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_config_resolved_for_claude_provider(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """resolve_mcp_config_path is called regardless of provider."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_LC_VERIFY}.verify_mcp_servers") as mock_mcp:
            mock_mcp.return_value = _mcp_servers_ok()
            execute_verify(_make_args(mcp_config=".mcp.json"))

        mock_resolve_mcp.assert_called_once()

    @patch(
        f"{_VERIFY}._run_mcp_edit_smoke_test",
        return_value="  MCP edit smoke test  [OK] edit verified",
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_servers_checked_for_claude_provider(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_smoke_test: MagicMock,
    ) -> None:
        """verify_mcp_servers is called when provider is claude and MCP config exists."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_ok()

        execute_verify(_make_args(mcp_config=".mcp.json"))

        mock_mcp_servers.assert_called_once_with("/fake/.mcp.json")

    @patch(
        f"{_VERIFY}._run_mcp_edit_smoke_test",
        return_value="  MCP edit smoke test  [OK] edit verified",
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_import_error_shows_info_message(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_smoke_test: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """ImportError from verify_mcp_servers prints info message and skips."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(
            f"{_LC_VERIFY}.verify_mcp_servers",
            side_effect=ImportError("No module named 'langchain_mcp_adapters'"),
        ):
            result = execute_verify(_make_args(mcp_config=".mcp.json"))

        output = capsys.readouterr().out
        assert "server health check skipped" in output
        assert "langchain-mcp-adapters not installed" in output
        assert result == 0  # informational only for claude

    def test_mcp_section_header_includes_library_name(self) -> None:
        """_format_mcp_section header contains library name."""
        symbols = {"success": "✓", "failure": "✗", "warning": "⚠"}
        mcp_result = _mcp_servers_ok()
        output = _format_mcp_section(mcp_result, symbols)
        assert "MCP SERVERS (via langchain-mcp-adapters)" in output

    @patch(
        f"{_VERIFY}._run_mcp_edit_smoke_test",
        return_value="  MCP edit smoke test  [OK] edit verified",
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_failure_informational_for_claude(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_smoke_test: MagicMock,
    ) -> None:
        """MCP failure does not affect exit code when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_fail()

        result = execute_verify(_make_args(mcp_config=".mcp.json"))

        assert result == 0  # MCP failure is informational for non-langchain

    @patch(f"{_VERIFY}._run_mcp_edit_smoke_test")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_mcp_edit_smoke_test_runs_for_claude_provider(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_smoke_test: MagicMock,
    ) -> None:
        """_run_mcp_edit_smoke_test is called for claude provider when MCP config exists."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_ok()
        mock_smoke_test.return_value = "  MCP edit smoke test  ✓ edit verified"

        execute_verify(_make_args(mcp_config=".mcp.json"))

        mock_smoke_test.assert_called_once()
        call_kwargs = mock_smoke_test.call_args
        assert call_kwargs[0][2] == "/fake/.mcp.json"  # mcp_config arg
