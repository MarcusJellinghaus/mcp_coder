"""Exit code matrix tests for the mcp-coder verify command (Step 6).

These tests exercise the full CLI path from main() through execute_verify(),
validating the exit code matrix across provider/mlflow scenarios.
"""

from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify_exit_code import _compute_exit_code
from mcp_coder.cli.main import main
from mcp_coder.llm.providers.langchain._config_diagnostics import ResolvedTarget

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
        mcp_config_path: str | None = None,
    ) -> int:
        """Run main() with mocked domain functions and return exit code.

        ``mcp_config_path`` overrides ``resolve_mcp_config_path`` (default None
        skips the MCP CONFIG block). When it points at a real ``.mcp.json``,
        ``_validate_mcp_config`` is left un-mocked so the real parse runs — the
        hard-fail short-circuit then keeps the un-mocked ``parse_claude_mcp_list``
        / ``verify_mcp_servers`` from being reached, so the case stays fast.
        """
        with (
            patch("sys.argv", ["mcp-coder", "verify"]),
            patch(
                f"{_VERIFY}.prompt_llm",
                return_value=_MOCK_LLM_RESPONSE,
            ),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(
                f"{_VERIFY}.resolve_mcp_config_path",
                return_value=mcp_config_path,
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

    def test_malformed_mcp_config_exit_1(self, tmp_path: Any) -> None:
        """Malformed .mcp.json -> real _validate_mcp_config -> exit 1 (full wiring).

        Exercises the end-to-end path: resolve_mcp_config_path points at a real
        malformed file, the un-mocked _validate_mcp_config returns False,
        mcp_config_ok threads into _compute_exit_code, and the CLI returns 1.
        """
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{not json", encoding="utf-8")
        assert (
            self._run_verify(
                provider=("claude", "default"),
                claude_ok=True,
                langchain_ok=None,
                mlflow_installed=False,
                mcp_config_path=str(mcp_json),
            )
            == 1
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


class TestMcpConfigExitCode:
    """Exit-code effect of the mcp_config_ok signal (provider-independent)."""

    def test_claude_active_mcp_config_fail_exit_1(self) -> None:
        """Exit 1 when mcp_config_ok=False and claude is active."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                mcp_config_ok=False,
            )
            == 1
        )

    def test_langchain_active_mcp_config_fail_exit_1(self) -> None:
        """Exit 1 when mcp_config_ok=False and langchain is active.

        Malformed .mcp.json breaks all providers, so the failure is
        provider-independent.
        """
        assert (
            _compute_exit_code(
                "langchain",
                _make_claude_result(),
                _make_langchain_result(),
                _make_mlflow_result(installed=False),
                mcp_config_ok=False,
            )
            == 1
        )

    def test_mcp_config_none_no_effect(self) -> None:
        """Exit 0 when mcp_config_ok=None (neutral / not checked)."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                mcp_config_ok=None,
            )
            == 0
        )

    def test_mcp_config_true_no_effect(self) -> None:
        """Exit 0 when mcp_config_ok=True (well-formed / empty)."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                mcp_config_ok=True,
            )
            == 0
        )


class TestJenkinsExitCode:
    """Exit-code effect of the jenkins_ok signal (gated on [jenkins] being set)."""

    def test_jenkins_fail_exit_1(self) -> None:
        """Exit 1 when jenkins_ok=False (configured and broken)."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                jenkins_ok=False,
            )
            == 1
        )

    def test_jenkins_none_no_effect(self) -> None:
        """Exit 0 when jenkins_ok=None ([jenkins] unconfigured -> neutral)."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                jenkins_ok=None,
            )
            == 0
        )

    def test_jenkins_true_no_effect(self) -> None:
        """Exit 0 when jenkins_ok=True."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                jenkins_ok=True,
            )
            == 0
        )


class TestContractViolationExitCode:
    """A contract violation must exit 1 through the *whole* CLI path.

    Unlike every other class here, ``verify_langchain`` is left un-mocked: the
    point is that a finding produced deep in the provider reaches
    ``overall_ok`` and then ``_compute_exit_code``. ``_load_langchain_config``
    is patched on the *verification* module, which holds its own binding from a
    module-level ``from . import`` — patching the package attribute would not
    be seen.
    """

    _CREDENTIAL_VARS = (
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_AD_TOKEN",
        "AZURE_OPENAI_ENDPOINT",
        "OPENAI_BASE_URL",
        "OPENAI_API_BASE",
    )

    def _run(self, config: dict[str, Any]) -> int:
        """Run main() with a real verify_langchain over *config*."""
        with (
            patch("sys.argv", ["mcp-coder", "verify"]),
            patch(f"{_VERIFY}.prompt_llm", return_value=_MOCK_LLM_RESPONSE),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
            patch(
                f"{_VERIFY}.resolve_llm_method",
                return_value=("langchain", "config.toml"),
            ),
            patch(f"{_LC_CONFIG}._load_langchain_config", return_value=config),
            patch(f"{_LC_VERIFY}._load_langchain_config", return_value=config),
            patch(f"{_LC_VERIFY}._check_package_installed", return_value=True),
            patch(
                f"{_LC_VERIFY}.resolve_target",
                return_value=ResolvedTarget("(not configured)", "unverified", False),
            ),
            patch(f"{_VERIFY}.verify_claude", return_value=_make_claude_result()),
            patch(
                f"{_VERIFY}.verify_mlflow",
                return_value=_make_mlflow_result(installed=False),
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

    def test_azure_without_base_url_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Case 1 end to end: exit 1, with the cause printed."""
        for var in self._CREDENTIAL_VARS:
            monkeypatch.delenv(var, raising=False)
        exit_code = self._run(
            {
                "provider": "langchain",
                "backend": "openai",
                "model": "gpt-4o",
                "api_key": "sk-abcd1234wxyz5678",
                "base_url": None,
                "api_version": "2024-02-01",
            }
        )
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "AZURE_OPENAI_ENDPOINT" in output

    def test_sound_config_still_exits_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The same path with the contract satisfied must not regress to 1."""
        for var in self._CREDENTIAL_VARS:
            monkeypatch.delenv(var, raising=False)
        assert (
            self._run(
                {
                    "provider": "langchain",
                    "backend": "openai",
                    "model": "gpt-4o",
                    "api_key": "sk-abcd1234wxyz5678",
                    "base_url": None,
                    "api_version": None,
                }
            )
            == 0
        )


class TestPromptsExitCode:
    """Exit-code effect of the prompts_ok signal (provider-independent).

    A configured prompt path that does not resolve is a misconfiguration
    whatever the active provider is, so this is a new exit-1 path for claude
    users too. The default stays ``True`` so every pre-existing call site and
    test keeps its exit code.
    """

    def test_claude_active_prompts_not_ok_exit_1(self) -> None:
        """Exit 1 when prompts_ok=False and claude is active."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                prompts_ok=False,
            )
            == 1
        )

    def test_langchain_active_prompts_not_ok_exit_1(self) -> None:
        """Exit 1 when prompts_ok=False and langchain is active."""
        assert (
            _compute_exit_code(
                "langchain",
                _make_claude_result(),
                _make_langchain_result(),
                _make_mlflow_result(installed=False),
                prompts_ok=False,
            )
            == 1
        )

    def test_prompts_ok_true_no_effect(self) -> None:
        """Exit 0 when prompts_ok=True (every prompt resolved)."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
                prompts_ok=True,
            )
            == 0
        )

    def test_prompts_ok_defaults_to_true(self) -> None:
        """Omitting the parameter is neutral, so existing callers are unchanged."""
        assert (
            _compute_exit_code(
                "claude",
                _make_claude_result(),
                None,
                _make_mlflow_result(installed=False),
            )
            == 0
        )
