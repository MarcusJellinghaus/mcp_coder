"""Tests for the _run_mcp_edit_smoke_test function in verify."""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (
    _run_mcp_edit_smoke_test,
    execute_verify,
)

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


def _mcp_ok() -> dict[str, Any]:
    return {
        "servers": {
            "mcp-tools-py": {"ok": True, "value": "5 tools available", "tools": 5},
        },
        "overall_ok": True,
    }


class TestMcpEditSmokeTest:
    """Tests for _run_mcp_edit_smoke_test function."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[FAIL]", "warning": "[WARN]"}

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

        assert "[WARN]" in result
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

        assert "[WARN]" in result
        assert "edit not verified" in result
        assert "timed out" in result

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_LC_VERIFY}.verify_mcp_servers")
    @patch(
        f"{_VERIFY}.resolve_mcp_config_path",
        return_value="/fake/.mcp.json",
    )
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_smoke_test_does_not_affect_exit_code(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_mcp_servers: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_verify_config: MagicMock,
        tmp_path: Path,
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

        exit_code = execute_verify(
            _make_args(mcp_config=".mcp.json", project_dir=str(tmp_path))
        )

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

    @patch(f"{_VERIFY}.verify_config")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(
        f"{_VERIFY}.resolve_mcp_config_path",
        return_value=None,
    )
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_smoke_test_skipped_when_no_mcp_config(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
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
