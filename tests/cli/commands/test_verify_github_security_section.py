"""Orchestration tests for the GITHUB SECURITY section (Step 3).

Exercises ``_print_github_security_section`` through ``execute_verify``:
section rendering, pass-through of API-backed rows, and exit-neutrality.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify

from .conftest import (
    _VERIFY,
    _claude_ok,
    _make_args,
    _minimal_llm_response,
    _mlflow_not_installed,
)

_SECTIONS = "mcp_coder.cli.commands.verify_sections"


def _security_api_ok() -> dict[str, Any]:
    row = {"ok": True, "value": "enabled", "severity": "warning"}
    return {
        "dependabot_alerts": dict(row),
        "dependabot_security_updates": dict(row),
        "secret_scanning": dict(row),
        "secret_scanning_push_protection": dict(row),
    }


def _security_api_fail() -> dict[str, Any]:
    row = {"ok": False, "value": "disabled", "severity": "warning"}
    return {
        "dependabot_alerts": dict(row),
        "dependabot_security_updates": dict(row),
        "secret_scanning": dict(row),
        "secret_scanning_push_protection": dict(row),
    }


class TestGithubSecuritySection:
    """Tests for the GITHUB SECURITY section wiring in execute_verify."""

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
    @patch(f"{_SECTIONS}.verify_github_security")
    def test_section_renders_all_rows(
        self,
        mock_security: MagicMock,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """All 7 GITHUB SECURITY rows render when the API-backed rows are all ok."""
        mock_security.return_value = _security_api_ok()
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "=== GITHUB SECURITY" in output
        for label in (
            "Dependabot config",
            "Dependabot alerts",
            "Dependabot security",
            "Secret scanning",
            "Secret push protection",
            "CodeQL workflow",
            "Code scanning alerts",
        ):
            assert label in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch(f"{_SECTIONS}._check_codeql_workflow")
    @patch(f"{_SECTIONS}._check_dependabot_config")
    @patch(f"{_SECTIONS}.verify_github_security")
    def test_section_is_exit_neutral_when_all_rows_fail(
        self,
        mock_security: MagicMock,
        mock_dependabot: MagicMock,
        mock_codeql: MagicMock,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """execute_verify still returns 0 when every GITHUB SECURITY row fails."""
        mock_security.return_value = _security_api_fail()
        mock_dependabot.return_value = {
            "ok": False,
            "value": "not present",
            "severity": "warning",
        }
        mock_codeql.return_value = {
            "ok": False,
            "value": "no workflow step uses github/codeql-action",
            "severity": "warning",
        }
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())

        assert result == 0

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch(f"{_SECTIONS}.verify_github_security")
    def test_api_result_rows_pass_through_unmodified(
        self,
        mock_security: MagicMock,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A 403-style ok=None row passes through and renders as [WARN]."""
        security = _security_api_ok()
        security["secret_scanning"] = {
            "ok": None,
            "value": "not accessible (403)",
            "severity": "warning",
        }
        mock_security.return_value = security
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        row = next(
            line for line in output.splitlines() if "not accessible (403)" in line
        )
        assert "[WARN]" in row

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch(f"{_SECTIONS}.verify_github_security")
    def test_no_token_rows_render_as_warn(
        self,
        mock_security: MagicMock,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """All four API-backed rows with ok=None/\"no token configured\" render as [WARN]."""
        row = {"ok": None, "value": "no token configured", "severity": "warning"}
        mock_security.return_value = {
            "dependabot_alerts": dict(row),
            "dependabot_security_updates": dict(row),
            "secret_scanning": dict(row),
            "secret_scanning_push_protection": dict(row),
        }
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())
        output = capsys.readouterr().out

        no_token_rows = [
            line for line in output.splitlines() if "no token configured" in line
        ]
        assert len(no_token_rows) == 4
        assert all("[WARN]" in line for line in no_token_rows)
        assert result == 0
