"""Tests for exit code logic and MCP server integration in verify."""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (
    _compute_exit_code,
    _format_mcp_section,
    _run_mcp_edit_smoke_test,
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


def _mcp_ok() -> dict[str, Any]:
    return {
        "servers": {
            "tools-py": {"ok": True, "value": "5 tools available", "tools": 5},
        },
        "overall_ok": True,
    }


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

    def test_test_prompt_failure_returns_exit_1(self) -> None:
        """Exit 1 when test_prompt_ok is False, regardless of provider/mlflow."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                test_prompt_ok=False,
            )
            == 1
        )

    def test_test_prompt_failure_with_mlflow_ok(self) -> None:
        """Exit 1 when test_prompt_ok is False even with MLflow enabled and ok."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_ok(),
                test_prompt_ok=False,
            )
            == 1
        )

    def test_test_prompt_ok_default_true(self) -> None:
        """Default test_prompt_ok=True does not affect exit code."""
        assert _compute_exit_code("claude", _claude_ok(), None, _mlflow_ok()) == 0

    def test_mcp_failure_langchain_returns_exit_1(self) -> None:
        """Exit 1 when langchain active and MCP servers failed."""
        mcp_fail = {"servers": {"bad": {"ok": False}}, "overall_ok": False}
        assert (
            _compute_exit_code(
                "langchain",
                _claude_ok(),
                _langchain_ok(),
                _mlflow_not_installed(),
                mcp_result=mcp_fail,
            )
            == 1
        )

    def test_mcp_failure_claude_does_not_affect_exit(self) -> None:
        """MCP failure ignored when provider is claude."""
        mcp_fail = {"servers": {"bad": {"ok": False}}, "overall_ok": False}
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                mcp_result=mcp_fail,
            )
            == 0
        )

    def test_mcp_none_does_not_affect_exit(self) -> None:
        """mcp_result=None (no config) does not affect exit code."""
        assert (
            _compute_exit_code(
                "langchain",
                _claude_ok(),
                _langchain_ok(),
                _mlflow_not_installed(),
                mcp_result=None,
            )
            == 0
        )

    def test_config_error_returns_exit_1(self) -> None:
        """Exit 1 when config_has_error=True, regardless of other results."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_ok(),
                config_has_error=True,
            )
            == 1
        )

    def test_config_no_error_does_not_affect_exit(self) -> None:
        """config_has_error=False does not change exit code (still 0 with ok results)."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                config_has_error=False,
            )
            == 0
        )


class TestMcpServersInVerify:
    """Tests for MCP server health check integration in execute_verify."""

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mcp_servers")
    @patch(
        "mcp_coder.cli.commands.verify.resolve_mcp_config_path",
        return_value="/fake/.mcp.json",
    )
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_mcp_servers_displayed_when_config_present(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """MCP SERVERS section shown when mcp_config is present."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_ok()

        execute_verify(_make_args(mcp_config=".mcp.json"))
        output = capsys.readouterr().out

        assert "MCP SERVERS" in output
        assert "tools-py" in output
        assert "5 tools available" in output
        mock_mcp_servers.assert_called_once_with("/fake/.mcp.json")

    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mcp_servers")
    @patch(
        "mcp_coder.cli.commands.verify.resolve_mcp_config_path",
        return_value=None,
    )
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_mcp_servers_skipped_when_no_config(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """MCP SERVERS section hidden when no MCP config."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "MCP SERVERS" not in output
        mock_mcp_servers.assert_not_called()


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
                "value": "/home/user/.config/mcp_coder/config.toml",
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

    @patch("mcp_coder.cli.commands.verify.verify_config")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_config_section_displayed_first(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
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

    @patch("mcp_coder.cli.commands.verify.verify_config")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_config_invalid_toml_causes_exit_1(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
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

    @patch("mcp_coder.cli.commands.verify.verify_config")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_config_missing_shows_warning(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
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


class TestMcpEditSmokeTest:
    """Tests for _run_mcp_edit_smoke_test function."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[FAIL]", "warning": "[!!]"}

    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    def test_smoke_test_pass_displays_ok(
        self,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Smoke test passes when prompt_llm writes B between A and C."""
        test_file = tmp_path / ".mcp_coder_verify.md"

        def fake_llm(*args: Any, **kwargs: Any) -> dict[str, Any]:
            test_file.write_text("A\nB\nC\n", encoding="utf-8")
            return {"text": "done"}

        mock_prompt_llm.side_effect = fake_llm

        result = _run_mcp_edit_smoke_test(
            tmp_path, "langchain", "/fake/.mcp.json", str(tmp_path), self._symbols()
        )

        assert "[OK]" in result
        assert "edit verified" in result

    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    def test_smoke_test_fail_displays_warning(
        self,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Smoke test warns when prompt_llm does not edit the file."""
        mock_prompt_llm.return_value = {"text": "done"}

        result = _run_mcp_edit_smoke_test(
            tmp_path, "langchain", "/fake/.mcp.json", str(tmp_path), self._symbols()
        )

        assert "[!!]" in result
        assert "edit not verified" in result

    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    def test_smoke_test_error_displays_warning(
        self,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Smoke test warns when prompt_llm raises an exception."""
        mock_prompt_llm.side_effect = TimeoutError("timed out")

        result = _run_mcp_edit_smoke_test(
            tmp_path, "langchain", "/fake/.mcp.json", str(tmp_path), self._symbols()
        )

        assert "[!!]" in result
        assert "edit not verified" in result
        assert "timed out" in result

    @patch("mcp_coder.cli.commands.verify.verify_config")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch("mcp_coder.cli.commands.verify.verify_mcp_servers")
    @patch(
        "mcp_coder.cli.commands.verify.resolve_mcp_config_path",
        return_value="/fake/.mcp.json",
    )
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_smoke_test_does_not_affect_exit_code(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
    ) -> None:
        """Smoke test failure does not affect exit code."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        # prompt_llm returns OK for test prompt but does not edit file
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_mcp_servers.return_value = _mcp_ok()
        mock_verify_config.return_value = {
            "entries": [],
            "has_error": False,
        }

        exit_code = execute_verify(_make_args(mcp_config=".mcp.json"))

        assert exit_code == 0

    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    def test_smoke_test_cleans_up_file(
        self,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test file is cleaned up after smoke test."""
        mock_prompt_llm.return_value = {"text": "done"}

        _run_mcp_edit_smoke_test(
            tmp_path, "langchain", "/fake/.mcp.json", str(tmp_path), self._symbols()
        )

        assert not (tmp_path / ".mcp_coder_verify.md").exists()

    @patch("mcp_coder.cli.commands.verify.verify_config")
    @patch("mcp_coder.cli.commands.verify.log_to_mlflow")
    @patch("mcp_coder.cli.commands.verify.prompt_llm")
    @patch(
        "mcp_coder.cli.commands.verify.resolve_mcp_config_path",
        return_value=None,
    )
    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    def test_smoke_test_skipped_when_no_mcp_config(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Smoke test line not in output when no mcp_config."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _claude_ok()
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_verify_config.return_value = {
            "entries": [],
            "has_error": False,
        }

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "MCP edit smoke test" not in output
