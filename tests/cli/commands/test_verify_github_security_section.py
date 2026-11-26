"""Orchestration test for the GITHUB SECURITY section.

The rows come from ``github_security_rows`` (mcp-workspace); this module only
checks that ``execute_verify`` prints the section and keeps it exit-neutral.
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

_SECURITY_KEYS = (
    "dependabot_config",
    "dependabot_alerts",
    "dependabot_security_updates",
    "secret_scanning",
    "secret_scanning_push_protection",
    "codeql_workflow",
    "code_scanning_alerts",
)


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
    def test_section_is_exit_neutral_when_all_rows_fail(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_github_security_rows: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """execute_verify still returns 0 when every GITHUB SECURITY row fails."""
        _mock_github_security_rows.return_value = {
            key: {"ok": False, "value": "disabled", "severity": "warning"}
            for key in _SECURITY_KEYS
        }
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())
        output = capsys.readouterr().out

        assert result == 0
        assert "=== GITHUB SECURITY" in output
