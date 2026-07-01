"""Exit code matrix tests for the mcp-coder verify command (Step 6).

These tests exercise the full CLI path from main() through execute_verify(),
validating the exit code matrix across provider/mlflow scenarios.
"""

from typing import Any
from unittest.mock import patch

from mcp_coder.cli.commands.verify import (
    STATUS_SYMBOLS,
    _compute_exit_code,
    _format_tools_exposed_section,
)
from mcp_coder.cli.main import main

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
# Exit code matrix tests
# ---------------------------------------------------------------------------

_MOCK_LLM_RESPONSE: dict[str, Any] = {
    "version": "1.0",
    "timestamp": "2026-01-01T00:00:00",
    "text": "OK",
    "session_id": None,
    "provider": "claude",
    "raw_response": {},
}


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
                f"{_VERIFY}.prompt_llm",
                return_value=_MOCK_LLM_RESPONSE,
            ),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(
                f"{_VERIFY}.resolve_mcp_config_path",
                return_value=None,
            ),
            patch(
                f"{_VERIFY}.resolve_llm_method",
                return_value=provider,
            ),
            patch(
                f"{_LC_CONFIG}._load_langchain_config",
                return_value={"backend": None},
            ),
            patch(
                f"{_VERIFY}.verify_claude",
                return_value=_make_claude_result(ok=claude_ok),
            ),
            patch(
                f"{_LC_VERIFY}.verify_langchain",
                return_value=_make_langchain_result(
                    ok=langchain_ok if langchain_ok is not None else True,
                ),
            ),
            patch(
                f"{_VERIFY}.verify_mlflow",
                return_value=_make_mlflow_result(
                    installed=mlflow_installed,
                    enabled=mlflow_enabled,
                    healthy=mlflow_healthy,
                ),
            ),
            patch(
                f"{_VERIFY}.verify_github",
                return_value={
                    "token_configured": {"ok": True, "value": "configured"},
                    "overall_ok": True,
                },
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


class TestToolsExposedExitCode:
    """Exit-code effect of the tools_exposed_ok signal (claude only)."""

    def test_claude_active_tools_exposed_fail_exit_1(self) -> None:
        """Exit 1 when tools_exposed_ok=False and claude is active."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                tools_exposed_ok=False,
            )
            == 1
        )

    def test_claude_active_tools_exposed_none_no_effect(self) -> None:
        """Exit 0 when tools_exposed_ok=None (neutral) and claude is active."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                tools_exposed_ok=None,
            )
            == 0
        )

    def test_langchain_active_tools_exposed_fail_no_effect(self) -> None:
        """Exit 0 when tools_exposed_ok=False but langchain is active."""
        assert (
            _compute_exit_code(
                "langchain",
                _make_claude_result(),
                _make_langchain_result(),
                _make_mlflow_result(installed=False),
                tools_exposed_ok=False,
            )
            == 0
        )


class TestFormatToolsExposedSection:
    """Tests for the _format_tools_exposed_section helper."""

    def test_connected_with_tools_ok(self) -> None:
        """Connected servers exposing >=1 tool -> [OK], ok True, names shown."""
        system_message = {
            "mcp_servers": [
                {"name": "mcp-tools-py", "status": "connected"},
                {"name": "mcp-workspace", "status": "connected"},
            ],
            "tools": ["mcp__tools__a", "mcp__workspace__b", "ToolSearch"],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is True
        assert STATUS_SYMBOLS["success"] in text
        assert "2" in text
        assert "mcp-tools-py" in text
        assert "mcp-workspace" in text
        assert "alwaysLoad" not in text

    def test_connected_zero_tools_fail_with_hint(self) -> None:
        """Connected but 0 tools -> [ERR], ok False, alwaysLoad hint."""
        system_message = {
            "mcp_servers": [{"name": "mcp-tools-py", "status": "connected"}],
            "tools": [],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is False
        assert STATUS_SYMBOLS["failure"] in text
        assert "alwaysLoad" in text

    def test_pending_server_warn(self) -> None:
        """A pending server -> [WARN], ok None, no alwaysLoad hint."""
        system_message = {
            "mcp_servers": [{"name": "mcp-tools-py", "status": "pending"}],
            "tools": [],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is None
        assert STATUS_SYMBOLS["warning"] in text
        assert "alwaysLoad" not in text

    def test_failed_server_fail_generic_hint(self) -> None:
        """A failed (fatal) server -> [ERR], ok False, generic hint only."""
        system_message = {
            "mcp_servers": [{"name": "mcp-tools-py", "status": "failed"}],
            "tools": [],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is False
        assert STATUS_SYMBOLS["failure"] in text
        assert "alwaysLoad" not in text
        assert "logs" in text

    def test_none_system_message_warn(self) -> None:
        """None (no init event) -> [WARN], ok None."""
        lines, ok = _format_tools_exposed_section(None, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is None
        assert STATUS_SYMBOLS["warning"] in text
