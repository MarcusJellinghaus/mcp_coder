"""Tests for the verify CLI orchestrator's MCP verification paths."""

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (
    _DropUnexpandedWarnings,
    _validate_mcp_config,
    execute_verify,
)
from mcp_coder.cli.commands.verify_formatting import _format_mcp_section
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

from .conftest import (
    _LC_VERIFY,
    _VERIFY,
    _claude_ok,
    _github_ok_default,
    _make_args,
    _mcp_servers_fail,
    _mcp_servers_ok,
    _minimal_llm_response,
    _mlflow_not_installed,
)


class TestVerifyMcpAllProviders:
    """Tests for provider-independent MCP verification + ImportError handling."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_validate_mcp(self) -> Any:
        """Default: treat any resolved (fake) .mcp.json as well-formed.

        These tests exercise downstream MCP health checks with fake config
        paths; mocking the validator prevents the hard-fail short-circuit from
        skipping them. Harmless when resolve returns None (never called).
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
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
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
        _mock_prepare_env: MagicMock,
        _mock_claude_mcp: MagicMock,
        mock_smoke_test: MagicMock,
    ) -> None:
        """verify_mcp_servers is called when provider is claude and MCP config exists."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_ok()

        execute_verify(_make_args(mcp_config=".mcp.json"))

        mock_mcp_servers.assert_called_once_with("/fake/.mcp.json", env_vars={"K": "V"})

    @patch(
        f"{_VERIFY}._run_mcp_edit_smoke_test",
        return_value="  MCP edit smoke test  [OK] edit verified",
    )
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
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
        mock_env: MagicMock,
        mock_parse: MagicMock,
        mock_smoke_test: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """ImportError from verify_mcp_servers prints info message and skips."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_parse.return_value = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]

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
    @patch(f"{_VERIFY}.parse_claude_mcp_list")
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={"K": "V"})
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
        mock_env: MagicMock,
        mock_parse: MagicMock,
        mock_smoke_test: MagicMock,
    ) -> None:
        """MCP failure does not affect exit code when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_fail()
        mock_parse.return_value = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]

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

    @patch(
        f"{_VERIFY}._run_mcp_edit_smoke_test",
        return_value="  MCP edit smoke test  [OK] edit verified",
    )
    @patch(f"{_VERIFY}.parse_claude_mcp_list", return_value=[])
    @patch(
        f"{_VERIFY}.prepare_llm_environment",
        return_value={
            "MCP_CODER_PROJECT_DIR": "/proj",
            "MCP_CODER_VENV_DIR": "/venv",
            "MCP_CODER_VENV_PATH": "/venv/Scripts",
        },
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value="/fake/.mcp.json")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_env_vars_passed_to_smoke_test_and_test_prompt(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_prepare_env: MagicMock,
        _mock_claude_mcp: MagicMock,
        mock_smoke_test: MagicMock,
    ) -> None:
        """env_vars from prepare_llm_environment flow to smoke test + test prompt.

        Without these, MCP servers can't expand ${MCP_CODER_VENV_PATH} etc. in
        .mcp.json, mirroring the env that icoder threads through RuntimeInfo.
        """
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_servers_ok()

        execute_verify(_make_args(mcp_config=".mcp.json"))

        expected_env = {
            "MCP_CODER_PROJECT_DIR": "/proj",
            "MCP_CODER_VENV_DIR": "/venv",
            "MCP_CODER_VENV_PATH": "/venv/Scripts",
        }
        # Smoke test received env_vars (kwarg)
        smoke_kwargs = mock_smoke_test.call_args.kwargs
        assert smoke_kwargs.get("env_vars") == expected_env
        # Unified test prompt received env_vars (kwarg)
        prompt_kwargs = mock_prompt_llm.call_args.kwargs
        assert prompt_kwargs.get("env_vars") == expected_env


class TestMcpConfigWarnings:
    """Tests for ``_validate_mcp_config`` parser and rendered warnings section."""

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    def test_valid_non_empty_servers(self, tmp_path: Path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(
            json.dumps({"mcpServers": {"srv": {"env": {"PATH": "/usr/bin"}}}}),
            encoding="utf-8",
        )
        assert _validate_mcp_config(str(p)) == (True, "well-formed", [])

    def test_empty_servers_returns_warn(self, tmp_path: Path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
        ok, message, warnings = _validate_mcp_config(str(p))
        assert ok is None
        assert warnings == []
        assert "no servers" in message

    def test_unparseable_json_hard_fails(self, tmp_path: Path) -> None:
        """Malformed JSON is a hard fail (the old silent swallow is fixed)."""
        p = tmp_path / ".mcp.json"
        p.write_text("{not json", encoding="utf-8")
        ok, message, warnings = _validate_mcp_config(str(p))
        assert ok is False
        assert warnings == []
        assert "invalid JSON" in message

    def test_missing_file_hard_fails(self, tmp_path: Path) -> None:
        """A missing file surfaces as an OSError -> hard fail (not swallowed)."""
        ok, _message, warnings = _validate_mcp_config(str(tmp_path / "nope.json"))
        assert ok is False
        assert warnings == []

    def test_mcpservers_not_an_object_hard_fails(self, tmp_path: Path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(json.dumps({"mcpServers": []}), encoding="utf-8")
        ok, message, warnings = _validate_mcp_config(str(p))
        assert ok is False
        assert warnings == []
        assert "mcpServers" in message

    @pytest.mark.parametrize("payload", ["[]", "42", '"foo"'])
    def test_top_level_not_an_object_hard_fails(
        self, tmp_path: Path, payload: str
    ) -> None:
        """Valid JSON whose top level is not an object must not crash on .get."""
        p = tmp_path / ".mcp.json"
        p.write_text(payload, encoding="utf-8")
        ok, _message, warnings = _validate_mcp_config(str(p))
        assert ok is False
        assert warnings == []

    def test_unresolved_placeholder_found(self, tmp_path: Path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "mcp-tools-py": {
                            "env": {"PYTHONPATH": "${MCP_CODER_PROJECT_DIR}/src"}
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        ok, _message, warnings = _validate_mcp_config(str(p))
        assert ok is True
        assert warnings == [
            ("mcp-tools-py / PYTHONPATH", "${MCP_CODER_PROJECT_DIR}/src")
        ]

    def test_no_placeholders_returns_no_warnings(self, tmp_path: Path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(
            json.dumps({"mcpServers": {"srv": {"env": {"PATH": "/usr/bin"}}}}),
            encoding="utf-8",
        )
        ok, _message, warnings = _validate_mcp_config(str(p))
        assert ok is True
        assert warnings == []

    def test_multiple_servers_multiple_vars(self, tmp_path: Path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "srv-a": {"env": {"PYTHONPATH": "${VAR_A}/src"}},
                        "srv-b": {"env": {"LIBPATH": "${VAR_B}\\Lib\\"}},
                    }
                }
            ),
            encoding="utf-8",
        )
        ok, _message, warnings = _validate_mcp_config(str(p))
        assert ok is True
        assert warnings == [
            ("srv-a / PYTHONPATH", "${VAR_A}/src"),
            ("srv-b / LIBPATH", "${VAR_B}\\Lib\\"),
        ]

    @patch(f"{_VERIFY}._run_mcp_edit_smoke_test", return_value="  smoke")
    @patch(f"{_VERIFY}.parse_claude_mcp_list", return_value=[])
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={})
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_section_omitted_when_clean(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_env: MagicMock,
        _mock_parse: MagicMock,
        _mock_smoke: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``.mcp.json`` has no placeholders, section is omitted."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(
            json.dumps({"mcpServers": {"srv": {"env": {"PATH": "/usr/bin"}}}}),
            encoding="utf-8",
        )
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_mcp_servers.return_value = _mcp_servers_ok()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=str(mcp_json)):
            execute_verify(_make_args(mcp_config=str(mcp_json)))
        output = capsys.readouterr().out
        assert "MCP CONFIG WARNINGS" not in output

    @patch(f"{_VERIFY}._run_mcp_edit_smoke_test", return_value="  smoke")
    @patch(f"{_VERIFY}.parse_claude_mcp_list", return_value=[])
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={})
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_section_rendered_when_findings(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_env: MagicMock,
        _mock_parse: MagicMock,
        _mock_smoke: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Section header and finding row are printed when unresolved vars exist."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "mcp-tools-py": {
                            "env": {"PYTHONPATH": "${MCP_CODER_PROJECT_DIR}/src"}
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_mcp_servers.return_value = _mcp_servers_ok()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=str(mcp_json)):
            execute_verify(_make_args(mcp_config=str(mcp_json)))
        output = capsys.readouterr().out
        assert "MCP CONFIG WARNINGS" in output
        assert "mcp-tools-py / PYTHONPATH" in output
        assert "${MCP_CODER_PROJECT_DIR}/src" in output

    @patch(f"{_VERIFY}._run_mcp_edit_smoke_test", return_value="  smoke")
    @patch(f"{_VERIFY}.parse_claude_mcp_list", return_value=[])
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={})
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_log_filter_suppresses_unexpanded_warning(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_env: MagicMock,
        _mock_parse: MagicMock,
        _mock_smoke: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The scoped log filter drops 'unexpanded variable' records from stdout."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        def _emit_warning_then_return(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            logging.getLogger("langchain_mcp_adapters").warning(
                "env['PYTHONPATH'] contains unexpanded variable reference: 'X'"
            )
            return _mcp_servers_ok()

        mock_mcp_servers.side_effect = _emit_warning_then_return

        handler = logging.StreamHandler()
        lc_logger = logging.getLogger("langchain_mcp_adapters")
        lc_logger.addHandler(handler)
        try:
            with patch(
                f"{_VERIFY}.resolve_mcp_config_path", return_value=str(mcp_json)
            ):
                execute_verify(_make_args(mcp_config=str(mcp_json)))
        finally:
            lc_logger.removeHandler(handler)

        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "unexpanded variable" not in combined

        # Filter is removed after execute_verify returns: ensure no lingering filter.
        assert not any(
            isinstance(f, _DropUnexpandedWarnings) for f in lc_logger.filters
        )


class TestMcpConfigWarningsDynamicWidth:
    """Tests for per-section dynamic label width in MCP CONFIG WARNINGS."""

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    @patch(f"{_VERIFY}._run_mcp_edit_smoke_test", return_value="  smoke")
    @patch(f"{_VERIFY}.parse_claude_mcp_list", return_value=[])
    @patch(f"{_VERIFY}.prepare_llm_environment", return_value={})
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_long_label_widens_section_value_column(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_env: MagicMock,
        _mock_parse: MagicMock,
        _mock_smoke: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A long label widens the section's value column; rows align consistently."""
        from mcp_coder.cli.commands.verify_formatting import (
            _LABEL_WIDTH,
            _MARKER_SLOT_WIDTH,
        )

        long_server = "langchain-mcp-adapters"
        short_server = "srv"
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        long_server: {"env": {"PYTHONPATH": "${VAR_A}/src"}},
                        short_server: {"env": {"X": "${VAR_B}"}},
                    }
                }
            ),
            encoding="utf-8",
        )
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_mcp_servers.return_value = _mcp_servers_ok()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=str(mcp_json)):
            execute_verify(_make_args(mcp_config=str(mcp_json)))

        output = capsys.readouterr().out
        lines = output.splitlines()
        long_label = f"{long_server} / PYTHONPATH"
        short_label = f"{short_server} / X"
        long_line = next(l for l in lines if long_label in l)
        short_line = next(l for l in lines if short_label in l)

        # All rows in this section align at the same value column.
        assert long_line.index("${VAR_A}") == short_line.index("${VAR_B}")

        # That column equals 2 + max_label_len + 1 + _MARKER_SLOT_WIDTH + 1.
        section_label_width = max(_LABEL_WIDTH, len(long_label))
        expected_col = 2 + section_label_width + 1 + _MARKER_SLOT_WIDTH + 1
        assert long_line.index("${VAR_A}") == expected_col
