"""Tests for verify CLI orchestrator section wiring (config, git, github, claude)."""

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import _DropUnexpandedWarnings, execute_verify
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

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
    _mlflow_not_installed,
)


class TestMcpConfigValidityRow:
    """Tests for the always-on MCP CONFIG validity row + hard-fail short-circuit."""

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    def _run(
        self,
        tmp_path: Path,
        content: str,
        capsys: pytest.CaptureFixture[str],
    ) -> tuple[int, str]:
        """Run execute_verify against a real temp ``.mcp.json``; return (exit, output).

        Leaves ``_validate_mcp_config`` un-mocked so the real parse runs against
        ``content``; downstream MCP functions are mocked so the OK/WARN paths
        render cleanly (and, on hard-fail, are provably not reached).
        """
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(content, encoding="utf-8")
        with (
            patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
            patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_VERIFY}.prepare_llm_environment", return_value={}),
            patch(
                f"{_VERIFY}.parse_claude_mcp_list",
                return_value=[
                    ClaudeMCPStatus(
                        name="mcp-tools-py", status_text="Connected", ok=True
                    ),
                ],
            ),
            patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
            patch(f"{_VERIFY}._run_mcp_edit_smoke_test", return_value="  smoke"),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=str(mcp_json)),
            patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_servers_ok()),
        ):
            result = execute_verify(_make_args(mcp_config=str(mcp_json)))
        return result, capsys.readouterr().out

    @staticmethod
    def _header_index(lines: list[str], prefix: str) -> int:
        return next(i for i, line in enumerate(lines) if line.startswith(prefix))

    def test_valid_config_ok_row_before_mcp_servers(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A valid config renders a ``[OK]`` row that precedes the MCP SERVERS section."""
        content = json.dumps({"mcpServers": {"srv": {"command": "x"}}})
        result, output = self._run(tmp_path, content, capsys)
        lines = output.splitlines()

        config_row = next(l for l in lines if ".mcp.json" in l)
        assert "[OK]" in config_row
        assert "well-formed" in config_row

        # The validity header prints before the MCP SERVERS health-check section.
        config_hdr = self._header_index(lines, "=== MCP CONFIG =")
        servers_hdr = self._header_index(lines, "=== MCP SERVERS")
        assert config_hdr < servers_hdr
        assert result == 0

    def test_malformed_config_err_row_exit_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A malformed config surfaces a ``[ERR]`` row (not swallowed) and exit 1."""
        result, output = self._run(tmp_path, "{not json", capsys)
        config_row = next(l for l in output.splitlines() if ".mcp.json" in l)
        assert "[ERR]" in config_row
        assert "invalid JSON" in config_row
        assert result == 1

    def test_empty_config_warn_row_exit_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An empty ``mcpServers`` renders a ``[WARN]`` row and keeps exit 0."""
        content = json.dumps({"mcpServers": {}})
        result, output = self._run(tmp_path, content, capsys)
        config_row = next(l for l in output.splitlines() if ".mcp.json" in l)
        assert "[WARN]" in config_row
        assert result == 0

    def test_malformed_config_short_circuits_downstream(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A malformed config prints the ERR row but skips all downstream MCP checks."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{not json", encoding="utf-8")
        with (
            patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
            patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_VERIFY}.prepare_llm_environment", return_value={}),
            patch(f"{_VERIFY}.parse_claude_mcp_list") as mock_parse,
            patch(f"{_VERIFY}.prompt_llm") as mock_prompt,
            patch(f"{_VERIFY}._run_mcp_edit_smoke_test") as mock_smoke,
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=str(mcp_json)),
            patch(f"{_LC_VERIFY}.verify_mcp_servers") as mock_mcp_servers,
        ):
            result = execute_verify(_make_args(mcp_config=str(mcp_json)))
        output = capsys.readouterr().out

        # The single upstream diagnostic is printed...
        config_row = next(l for l in output.splitlines() if ".mcp.json" in l)
        assert "[ERR]" in config_row

        # ...and every downstream MCP check is short-circuited.
        mock_parse.assert_not_called()
        mock_mcp_servers.assert_not_called()
        mock_smoke.assert_not_called()
        mock_prompt.assert_not_called()
        assert "MCP SERVERS" not in output
        assert "Test prompt" not in output
        assert result == 1


class TestDropUnexpandedFilter:
    """Tests for the ``_DropUnexpandedWarnings`` logging filter."""

    def test_drops_unexpanded_message(self) -> None:
        f = _DropUnexpandedWarnings()
        rec = logging.LogRecord(
            "x",
            logging.WARNING,
            "",
            0,
            "env['PYTHONPATH'] contains unexpanded variable reference: 'X'",
            None,
            None,
        )
        assert f.filter(rec) is False

    def test_passes_other_messages(self) -> None:
        f = _DropUnexpandedWarnings()
        rec = logging.LogRecord(
            "x", logging.WARNING, "", 0, "normal warning", None, None
        )
        assert f.filter(rec) is True


class TestConditionalClaudeDisplay:
    """Tests for conditional Claude display based on active provider."""

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

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
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


def _github_ok() -> dict[str, Any]:
    """Return a GitHub verification result with overall_ok=True."""
    return {
        "token_configured": {"ok": True, "value": "ghp_***", "severity": "error"},
        "authenticated_user": {"ok": True, "value": "octocat", "severity": "error"},
        "repo_url": {"ok": True, "value": "owner/repo", "severity": "error"},
        "repo_accessible": {"ok": True, "value": "accessible", "severity": "error"},
        "branch_protection": {
            "ok": True,
            "value": "enabled",
            "severity": "warning",
        },
        "overall_ok": True,
    }


def _github_fail() -> dict[str, Any]:
    """Return a GitHub verification result with overall_ok=False."""
    return {
        "token_configured": {
            "ok": False,
            "value": "not set",
            "severity": "error",
            "install_hint": "pip install PyGithub",
        },
        "overall_ok": False,
    }


class TestVerifyGitHubOrchestration:
    """Tests for GitHub section wiring in execute_verify (Step 3)."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @patch(f"{_VERIFY}.verify_github")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_github_section_displayed_after_project(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_github: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """GITHUB section appears after PROJECT and before LLM PROVIDER."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_github.return_value = _github_ok()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "=== GITHUB" in output
        project_pos = output.index("PROJECT")
        github_pos = output.index("=== GITHUB")
        llm_pos = output.index("LLM PROVIDER")
        assert project_pos < github_pos < llm_pos

    @patch(f"{_VERIFY}.verify_github")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_verify_github_called_with_project_dir(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_github: MagicMock,
        tmp_path: Path,
    ) -> None:
        """verify_github is called with the resolved project_dir Path."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_github.return_value = _github_ok()

        execute_verify(_make_args(project_dir=str(tmp_path)))

        mock_github.assert_called_once_with(tmp_path)

    @patch(f"{_VERIFY}.verify_github")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_github_install_hints_collected(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_github: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Install hints from github_result appear in INSTALL INSTRUCTIONS."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_github.return_value = _github_fail()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "INSTALL INSTRUCTIONS" in output
        assert "PyGithub" in output

    @patch(f"{_VERIFY}.verify_github")
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_github_failure_causes_exit_1(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_github: MagicMock,
    ) -> None:
        """When verify_github returns overall_ok=False, exit code is 1."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()
        mock_github.return_value = _github_fail()

        result = execute_verify(_make_args())

        assert result == 1


class TestGitWiring:
    """Tests pinning the Git section's wiring into execute_verify."""

    def test_git_section_appears_between_project_and_github(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIT section is rendered between PROJECT and GITHUB (Decision #2)."""
        execute_verify(_make_args())
        output = capsys.readouterr().out
        assert (
            output.find("=== PROJECT")
            < output.find("=== GIT")
            < output.find("=== GITHUB")
        )

    def test_verify_git_called_with_actually_sign_true(self) -> None:
        """Decision #3: Tier 3 always runs (actually_sign=True, no flag)."""
        with patch(
            f"{_VERIFY}.verify_git", return_value={"overall_ok": True}
        ) as mock_verify_git:
            execute_verify(_make_args())
        mock_verify_git.assert_called_once()
        assert mock_verify_git.call_args.kwargs["actually_sign"] is True
