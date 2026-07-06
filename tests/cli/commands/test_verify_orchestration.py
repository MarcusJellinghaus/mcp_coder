"""Tests for the verify CLI orchestrator (Step 5 & 6)."""

import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify

from .conftest import (
    _LC_VERIFY,
    _VERIFY,
    _claude_ok,
    _github_ok_default,
    _langchain_fail,
    _langchain_ok,
    _make_args,
    _mcp_servers_ok,
    _minimal_llm_response,
    _mlflow_enabled_broken,
    _mlflow_not_installed,
    _mlflow_ok,
)


class TestVerifyOrchestration:
    """Tests for the verify CLI orchestrator."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_validate_mcp(self) -> Any:
        """Default: treat any resolved .mcp.json as well-formed.

        Tests here point ``resolve_mcp_config_path`` at fake paths; mocking the
        validator keeps the hard-fail short-circuit from swallowing downstream
        MCP checks. Harmless when no MCP config is resolved (never called).
        """
        with patch(
            f"{_VERIFY}._validate_mcp_config",
            return_value=(True, "well-formed", []),
        ):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
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
            "servers": {"mcp-tools-py": {"ok": True, "value": "5 tools", "tools": 5}},
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

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_github_section_renders_diagnostics(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """api_base_url row and token_fingerprint suffix appear in rendered output."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        github_with_diagnostics: dict[str, Any] = {
            "api_base_url": {"ok": True, "value": "https://api.example.ghe.com"},
            "token_configured": {
                "ok": True,
                "value": "configured (scopes: repo)",
                "token_source": "config",
                "token_fingerprint": "ghp_...a3f9",
            },
            "overall_ok": True,
        }
        with patch(f"{_VERIFY}.verify_github", return_value=github_with_diagnostics):
            execute_verify(_make_args())
        output = capsys.readouterr().out
        assert "API base URL" in output
        assert "https://api.example.ghe.com" in output
        assert "ghp_...a3f9" in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_github_section_renders_permission_probes(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """[Permissions] subsection reaches end-to-end rendered output."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        github_with_permissions: dict[str, Any] = {
            "perm_contents_read": {"ok": True, "value": "granted"},
            "perm_administration_read": {"ok": True, "value": "granted"},
            "perm_pull_requests_read": {"ok": True, "value": "granted"},
            "perm_issues_read": {"ok": True, "value": "granted"},
            "perm_workflows_read": {
                "ok": False,
                "value": "denied",
                "error": "https://docs.github.com/...#workflows",
            },
            "perm_statuses_read": {"ok": True, "value": "granted"},
            "overall_ok": True,
        }
        with patch(f"{_VERIFY}.verify_github", return_value=github_with_permissions):
            execute_verify(_make_args())
        output = capsys.readouterr().out
        assert "[Permissions]" in output
        assert "Actions: Read" in output


class TestVerifyTestPromptFailure:
    """Tests for improved test prompt failure output (Step 5A)."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
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
