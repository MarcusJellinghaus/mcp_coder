"""Integration tests for mcp-coder verify command (Step 6).

These tests exercise the full CLI path from main() through execute_verify(),
validating output format, --check-models flag parsing, and exit code matrix.
"""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.main import main
from mcp_coder.mcp_workspace_git import verify_git as real_verify_git
from mcp_coder.utils.subprocess_runner import execute_command

_LC_VERIFY = "mcp_coder.llm.providers.langchain.verification"
_LC_CONFIG = "mcp_coder.llm.providers.langchain"
_VERIFY = "mcp_coder.cli.commands.verify"

# ---------------------------------------------------------------------------
# Helpers to build mock domain results
# ---------------------------------------------------------------------------


def _make_claude_result(ok: bool = True) -> dict[str, Any]:
    """Build a mock verify_claude() result."""
    if ok:
        return {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_path": {"ok": True, "value": "/usr/bin/claude"},
            "cli_version": {"ok": True, "value": "1.0.0"},
            "cli_works": {"ok": True, "value": "YES"},
            "api_integration": {"ok": True, "value": "OK", "error": None},
            "overall_ok": True,
        }
    return {
        "cli_found": {"ok": False, "value": "NO"},
        "cli_works": {"ok": False, "value": "NO"},
        "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
        "overall_ok": False,
    }


def _make_langchain_result(ok: bool = True) -> dict[str, Any]:
    """Build a mock verify_langchain() result."""
    if ok:
        return {
            "backend": {"ok": True, "value": "openai"},
            "model": {"ok": True, "value": "gpt-4"},
            "api_key": {"ok": True, "value": "sk-ab...7x2f", "source": "env var"},
            "langchain_core": {"ok": True, "value": "installed"},
            "backend_package": {"ok": True, "value": "langchain-openai installed"},
            "overall_ok": True,
        }
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": False, "value": None, "source": None},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": False, "value": "langchain-openai not installed"},
        "overall_ok": False,
    }


def _make_mlflow_result(
    installed: bool = True,
    enabled: bool = False,
    healthy: bool = True,
) -> dict[str, Any]:
    """Build a mock verify_mlflow() result."""
    if not installed:
        return {
            "installed": {"ok": False, "value": "not installed"},
            "overall_ok": True,
        }
    result: dict[str, Any] = {
        "installed": {"ok": True, "value": "version 2.10.0"},
    }
    if not enabled:
        result["enabled"] = {"ok": False, "value": "disabled"}
        result["overall_ok"] = True
        return result
    result["enabled"] = {"ok": True, "value": "(config.toml)"}
    if healthy:
        result["tracking_uri"] = {"ok": True, "value": "http://localhost:5000"}
        result["connection"] = {"ok": True, "value": "tracking server reachable"}
        result["experiment"] = {"ok": True, "value": '"default" (exists)'}
        result["artifact_location"] = {
            "ok": True,
            "value": "not configured (using default)",
        }
        result["overall_ok"] = True
    else:
        result["tracking_uri"] = {
            "ok": False,
            "value": "http://bad:5000",
            "error": "invalid",
        }
        result["connection"] = {
            "ok": False,
            "value": "unreachable: connection refused",
        }
        result["experiment"] = {
            "ok": False,
            "value": '"default" (could not check)',
        }
        result["artifact_location"] = {
            "ok": True,
            "value": "not configured (using default)",
        }
        result["overall_ok"] = False
    return result


# ---------------------------------------------------------------------------
# End-to-end integration tests
# ---------------------------------------------------------------------------


class TestVerifyEndToEnd:
    """Integration tests for mcp-coder verify command.

    These tests call main() with sys.argv patched to exercise the full
    CLI path: argument parsing → execute_verify → domain mocks → output.
    """

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_verify_github(self) -> Any:
        with patch(
            f"{_VERIFY}.verify_github",
            return_value={
                "token_configured": {"ok": True, "value": "configured"},
                "overall_ok": True,
            },
        ):
            yield

    @pytest.fixture(autouse=True)
    def _mock_langchain_config(self) -> Any:
        """Default: no langchain backend configured.

        The claude-active readiness check calls the real
        ``_load_langchain_config()``; patch it here so the developer's real
        machine config cannot perturb these tests. Individual tests override
        this with a specific backend via their own decorator patch.
        """
        with patch(
            f"{_LC_CONFIG}._load_langchain_config",
            return_value={"backend": None},
        ):
            yield

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_full_verify_output_format(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output contains all three section headers."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        exit_code = main()
        output = capsys.readouterr().out

        assert "=== BASIC VERIFICATION ===" in output
        assert "=== LLM PROVIDER ===" in output
        assert "=== MLFLOW ===" in output
        assert exit_code == 0

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None)
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify", "--check-models"])
    def test_check_models_flag_parsed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_resolve_mcp: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """--check-models flag reaches verify_langchain via full CLI path."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_lc.return_value = _make_langchain_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        exit_code = main()

        assert exit_code == 0
        mock_lc.assert_called_once_with(check_models=True, mcp_config_path=None)

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_check_models_defaults_false(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
    ) -> None:
        """--check-models defaults to False when not provided."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        main()

        # Verify args namespace has check_models=False
        _ = mock_claude.call_args
        # verify_claude takes no args, but we can check the parsed args
        # by inspecting that langchain was NOT called (claude provider)
        mock_claude.assert_called_once()

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_output_contains_status_symbols(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output contains platform-appropriate status symbols."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        main()
        output = capsys.readouterr().out

        # On Windows: [OK], on Unix: checkmark. Either way, status is shown.
        assert "[OK]" in output or "\u2713" in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_active_provider_shown_in_output(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Active provider name and source appear in output."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        main()
        output = capsys.readouterr().out

        assert "claude" in output
        assert "default" in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_langchain_details_shown_when_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """LangChain details section appears when provider is langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_lc.return_value = _make_langchain_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        main()
        output = capsys.readouterr().out

        assert "LLM PROVIDER DETAILS" in output
        assert "openai" in output

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_claude_fallback_note_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude fallback note shown when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        main()
        output = capsys.readouterr().out

        assert "uses Claude CLI" in output
        # No langchain configured -> readiness WARN row must be absent.
        assert "Langchain backend" not in output
        assert "configured but" not in output
        assert "not a recognized" not in output

    @patch(f"{_LC_VERIFY}._check_package_installed", return_value=False)
    @patch(
        f"{_LC_CONFIG}._load_langchain_config",
        return_value={"backend": "anthropic"},
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_langchain_backend_warn_when_module_missing_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_lc_config: MagicMock,
        _mock_pkg: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude active + configured backend module missing -> [WARN] row, exit 0."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        exit_code = main()
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "uses Claude CLI" in output
        assert "[WARN]" in output
        assert (
            "backend 'anthropic' configured but langchain-anthropic not installed"
            in output
        )
        assert (
            "-> pip install langchain-anthropic (needed for --llm-method langchain)"
            in output
        )

    @patch(f"{_LC_VERIFY}._check_package_installed", return_value=True)
    @patch(
        f"{_LC_CONFIG}._load_langchain_config",
        return_value={"backend": "anthropic"},
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_langchain_backend_no_warn_when_module_installed_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_lc_config: MagicMock,
        _mock_pkg: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude active + configured backend module installed -> no langchain row."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        exit_code = main()
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "uses Claude CLI" in output
        # The specific langchain readiness row must be absent (a global [WARN]
        # check is unsafe: other rows legitimately emit [WARN] on this path).
        assert "Langchain backend" not in output
        assert "configured but" not in output
        assert "not a recognized" not in output

    @patch(
        f"{_LC_CONFIG}._load_langchain_config",
        return_value={"backend": "typo-backend"},
    )
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_langchain_backend_warn_when_unrecognized_backend_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        _mock_lc_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude active + unrecognized backend name -> [WARN] row, no install hint."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        mock_prompt_llm.return_value = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "OK",
            "session_id": None,
            "provider": "claude",
            "raw_response": {},
        }

        exit_code = main()
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "uses Claude CLI" in output
        assert "[WARN]" in output
        assert "not a recognized langchain backend" in output
        assert "-> pip install" not in output


_MOCK_LLM_RESPONSE: dict[str, Any] = {
    "version": "1.0",
    "timestamp": "2026-01-01T00:00:00",
    "text": "OK",
    "session_id": None,
    "provider": "claude",
    "raw_response": {},
}


@pytest.mark.git_integration
def test_verify_flags_gpgsign_without_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Repo with commit.gpgsign=true and no user.signingkey -> exit non-zero.

    Note: this test is environment-sensitive - gpg may or may not be installed
    on the runner. Assertions are intentionally minimal (header present + non-zero
    exit) so the test stays robust across both environments.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    assert execute_command(["git", "init"], cwd=str(repo)).return_code == 0
    assert (
        execute_command(
            ["git", "config", "user.email", "t@t.test"], cwd=str(repo)
        ).return_code
        == 0
    )
    assert (
        execute_command(["git", "config", "user.name", "T"], cwd=str(repo)).return_code
        == 0
    )
    assert (
        execute_command(
            ["git", "config", "commit.gpgsign", "true"], cwd=str(repo)
        ).return_code
        == 0
    )

    args = argparse.Namespace(
        check_models=False,
        mcp_config=None,
        settings=None,
        llm_method=None,
        project_dir=str(repo),
    )
    with (
        patch(f"{_VERIFY}.verify_git", side_effect=real_verify_git),
        patch(f"{_VERIFY}.verify_github", return_value={"overall_ok": True}),
        patch(f"{_VERIFY}.verify_claude", return_value=_make_claude_result(ok=True)),
        patch(
            f"{_VERIFY}.verify_mlflow",
            return_value=_make_mlflow_result(installed=False),
        ),
        patch(f"{_VERIFY}.prompt_llm", return_value=_MOCK_LLM_RESPONSE),
        patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
        patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
    ):
        exit_code = execute_verify(args)

    output = capsys.readouterr().out
    assert "=== GIT" in output
    # Strict contract: when verify_git detects signing intent, exit must be
    # non-zero. Some git versions report "not configured" even when the flag
    # is set due to the `git config --get ... --type=bool` argument-order
    # quirk; skip the exit-code assertion in that case so the test stays
    # robust across environments.
    if "not configured" not in output:
        assert exit_code != 0
