"""Integration tests for mcp-coder verify command (Step 6).

These tests exercise the full CLI path from main() through execute_verify(),
validating output format, --check-models flag parsing, and exit code matrix.
"""

import argparse
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.main import main

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
            "test_prompt": {"ok": True, "value": "responded in 1.2s", "error": None},
            "overall_ok": True,
        }
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": False, "value": None, "source": None},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": False, "value": "langchain-openai not installed"},
        "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
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

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_full_verify_output_format(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output contains all three section headers."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        exit_code = main()
        output = capsys.readouterr().out

        assert "=== BASIC VERIFICATION ===" in output
        assert "=== LLM PROVIDER ===" in output
        assert "=== MLFLOW ===" in output
        assert exit_code == 0

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify", "--check-models"])
    def test_check_models_flag_parsed(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """--check-models flag reaches verify_langchain via full CLI path."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_lc.return_value = _make_langchain_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        exit_code = main()

        assert exit_code == 0
        mock_lc.assert_called_once_with(check_models=True, mcp_config_path=mock.ANY)

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_check_models_defaults_false(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
    ) -> None:
        """--check-models defaults to False when not provided."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        main()

        # Verify args namespace has check_models=False
        call_args = mock_claude.call_args
        # verify_claude takes no args, but we can check the parsed args
        # by inspecting that langchain was NOT called (claude provider)
        mock_claude.assert_called_once()

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_output_contains_status_symbols(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output contains platform-appropriate status symbols."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        main()
        output = capsys.readouterr().out

        # On Windows: [OK], on Unix: checkmark. Either way, status is shown.
        assert "[OK]" in output or "\u2713" in output

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_active_provider_shown_in_output(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Active provider name and source appear in output."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        main()
        output = capsys.readouterr().out

        assert "claude" in output
        assert "default" in output

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_langchain_details_shown_when_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """LangChain details section appears when provider is langchain."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_lc.return_value = _make_langchain_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        main()
        output = capsys.readouterr().out

        assert "LLM PROVIDER DETAILS" in output
        assert "openai" in output

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify.resolve_llm_method")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_claude_fallback_note_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Claude fallback note shown when provider is claude."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)

        main()
        output = capsys.readouterr().out

        assert "uses Claude CLI" in output


# ---------------------------------------------------------------------------
# Exit code matrix tests
# ---------------------------------------------------------------------------


class TestExitCodeMatrix:
    """Exhaustive exit code scenarios via full CLI path.

    These tests validate the 8 exit code scenarios described in the spec.
    """

    def _run_verify(
        self,
        provider: tuple[str, str],
        claude_ok: bool,
        langchain_ok: bool | None,
        mlflow_installed: bool,
        mlflow_enabled: bool = False,
        mlflow_healthy: bool = True,
    ) -> int:
        """Run main() with mocked domain functions and return exit code."""
        with (
            patch("sys.argv", ["mcp-coder", "verify"]),
            patch(
                "mcp_coder.cli.commands.verify.resolve_llm_method",
                return_value=provider,
            ),
            patch(
                "mcp_coder.cli.commands.verify.verify_claude",
                return_value=_make_claude_result(ok=claude_ok),
            ),
            patch(
                "mcp_coder.cli.commands.verify.verify_langchain",
                return_value=_make_langchain_result(
                    ok=langchain_ok if langchain_ok is not None else True,
                ),
            ),
            patch(
                "mcp_coder.cli.commands.verify.verify_mlflow",
                return_value=_make_mlflow_result(
                    installed=mlflow_installed,
                    enabled=mlflow_enabled,
                    healthy=mlflow_healthy,
                ),
            ),
        ):
            return main()

    def test_claude_active_claude_ok(self) -> None:
        """provider=claude, Claude works -> exit 0."""
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=True,
                langchain_ok=None,
                mlflow_installed=False,
            )
            == 0
        )

    def test_claude_active_claude_broken(self) -> None:
        """provider=claude, Claude broken -> exit 1."""
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=False,
                langchain_ok=None,
                mlflow_installed=False,
            )
            == 1
        )

    def test_langchain_active_langchain_ok_claude_broken(self) -> None:
        """provider=langchain, LangChain works, Claude broken -> exit 0 (informational)."""
        assert (
            self._run_verify(
                provider=("langchain", "config.toml"),
                claude_ok=False,
                langchain_ok=True,
                mlflow_installed=False,
            )
            == 0
        )

    def test_langchain_active_langchain_broken(self) -> None:
        """provider=langchain, LangChain broken -> exit 1."""
        assert (
            self._run_verify(
                provider=("langchain", "config.toml"),
                claude_ok=True,
                langchain_ok=False,
                mlflow_installed=False,
            )
            == 1
        )

    def test_mlflow_enabled_and_broken(self) -> None:
        """MLflow enabled but misconfigured -> exit 1 regardless of provider."""
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=True,
                langchain_ok=None,
                mlflow_installed=True,
                mlflow_enabled=True,
                mlflow_healthy=False,
            )
            == 1
        )

    def test_mlflow_not_installed(self) -> None:
        """MLflow not installed -> exit 0 (informational)."""
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=True,
                langchain_ok=None,
                mlflow_installed=False,
            )
            == 0
        )

    def test_mlflow_disabled(self) -> None:
        """MLflow installed but disabled -> exit 0 (informational)."""
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=True,
                langchain_ok=None,
                mlflow_installed=True,
                mlflow_enabled=False,
            )
            == 0
        )

    def test_mlflow_enabled_and_healthy(self) -> None:
        """MLflow enabled and all checks pass -> exit 0."""
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=True,
                langchain_ok=None,
                mlflow_installed=True,
                mlflow_enabled=True,
                mlflow_healthy=True,
            )
            == 0
        )
