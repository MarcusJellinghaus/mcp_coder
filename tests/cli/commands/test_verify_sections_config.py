"""Tests for the verify config-echo, provider-env and TLS/proxy rows.

Split out of ``test_verify_sections_orchestration.py``: the step-7/14/17
sections (effective-config echo, ``MCP_CODER_LLM_PROVIDER`` visibility and the
ENVIRONMENT TLS/proxy summary) all report *configuration* rather than the
per-domain verification wiring the sibling module covers.
"""

from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import STATUS_SYMBOLS
from mcp_coder.cli.commands.verify_sections import _print_environment_section

from .conftest import (
    _LC_VERIFY,
    _VERIFY,
    _assert_value_at_column,
    _claude_ok,
    _expected_value_column,
    _github_ok_default,
    _langchain_ok,
    _make_args,
    _minimal_llm_response,
    _mlflow_not_installed,
)


def _langchain_with_echo() -> dict[str, Any]:
    """A langchain result carrying the list-valued effective-config echo."""
    result = _langchain_ok()
    result["effective_config"] = [
        ("backend", "openai"),
        ("mode", "plain openai (api_version not set)"),
        ("model", "gpt-4"),
        ("base_url", "https://api.openai.com/v1/   (SDK default)"),
        ("api_key", "sk-ab...7x2f   (from OPENAI_API_KEY env var)"),
    ]
    return result


class TestEffectiveConfigSection:
    """The echo prints as its own symbol-free section (step 7, TDD 5)."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    def _run(
        self, lc_result: dict[str, Any], capsys: pytest.CaptureFixture[str]
    ) -> tuple[int, str]:
        with (
            patch(f"{_VERIFY}.find_claude_executable", return_value=None),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_LC_VERIFY}.verify_langchain", return_value=lc_result),
            patch(
                f"{_VERIFY}.resolve_llm_method",
                return_value=("langchain", "config.toml"),
            ),
        ):
            result = execute_verify(_make_args())
        return result, capsys.readouterr().out

    def test_echo_rendered_without_status_symbols(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        result, output = self._run(_langchain_with_echo(), capsys)

        start = output.index("=== EFFECTIVE CONFIG")
        end = output.index("=== LLM PROVIDER DETAILS")
        block = output[start:end]

        assert "plain openai (api_version not set)" in block
        assert "https://api.openai.com/v1/   (SDK default)" in block
        for symbol in ("[OK]", "[ERR]", "[WARN]"):
            assert symbol not in block
        assert result == 0

    def test_echo_is_not_part_of_provider_details(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A list-valued entry is skipped by _format_section entirely."""
        _result, output = self._run(_langchain_with_echo(), capsys)
        details = output[output.index("=== LLM PROVIDER DETAILS") :]

        assert "effective_config" not in output
        assert "plain openai" not in details

    def test_no_section_when_the_result_omits_the_echo(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _result, output = self._run(_langchain_ok(), capsys)

        assert "EFFECTIVE CONFIG" not in output

    def test_flag_rows_warn_without_changing_the_exit_code(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lc_result = _langchain_with_echo()
        lc_result["base_url_redirect"] = {
            "ok": None,
            "value": "OPENAI_BASE_URL overrides config.toml — requests go to https://h/v1",
        }
        lc_result["api_key_override"] = {
            "ok": None,
            "value": "OPENAI_API_KEY env var overrides [llm.langchain] api_key in config.toml",
        }
        result, output = self._run(lc_result, capsys)
        details = output[output.index("=== LLM PROVIDER DETAILS") :]

        redirect_row = next(l for l in details.splitlines() if "Base URL redirect" in l)
        override_row = next(l for l in details.splitlines() if "API key override" in l)
        assert "[WARN]" in redirect_row
        assert "[WARN]" in override_row
        assert result == 0


class TestProviderEnvVarVisibility:
    """`MCP_CODER_LLM_PROVIDER` is surfaced when it did NOT decide the provider.

    Step 14 / Decision 23: after step 12 the variable no longer silently wins
    over ``--llm-method``, so a user who exported it needs to be told it was
    seen and overridden. Exit-neutral: printed only.
    """

    _LABEL = "MCP_CODER_LLM_PROVIDER"

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    def _run(
        self,
        resolved: tuple[str, str],
        capsys: pytest.CaptureFixture[str],
        **args_kwargs: Any,
    ) -> tuple[int, str]:
        """Run execute_verify with ``resolve_llm_method`` pinned to ``resolved``."""
        with (
            patch(f"{_VERIFY}.find_claude_executable", return_value=None),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
            patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok()),
            patch(f"{_VERIFY}.resolve_llm_method", return_value=resolved),
        ):
            result = execute_verify(_make_args(**args_kwargs))
        return result, capsys.readouterr().out

    def _env_rows(self, output: str) -> list[str]:
        return [line for line in output.splitlines() if self._LABEL in line]

    def test_env_set_but_cli_flag_wins_warns(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 1: overridden by --llm-method → WARN row naming what overrode it."""
        monkeypatch.setenv(self._LABEL, "claude")
        result, output = self._run(
            ("langchain", "cli argument"), capsys, llm_method="langchain"
        )

        row = next(iter(self._env_rows(output)))
        assert "[WARN]" in row
        assert "set to 'claude'" in row
        assert "cli argument" in row
        assert "using 'langchain'" in row
        # The variable is emphatically NOT the source here.
        assert "source" not in row
        # Exit-neutral.
        assert result == 0

    def test_warning_row_aligns_with_active_provider_row(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The long label gets an explicit label_width so the columns line up."""
        monkeypatch.setenv(self._LABEL, "claude")
        _result, output = self._run(
            ("langchain", "cli argument"), capsys, llm_method="langchain"
        )

        warn_row = next(iter(self._env_rows(output)))
        _assert_value_at_column(
            warn_row, _expected_value_column(2, label_width=len(self._LABEL))
        )

    def test_env_set_and_is_the_source_adds_no_row(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 2: the Active provider row already names it — nothing extra."""
        monkeypatch.setenv(self._LABEL, "langchain")
        result, output = self._run(("langchain", "env MCP_CODER_LLM_PROVIDER"), capsys)

        active_row = next(
            line for line in output.splitlines() if "Active provider" in line
        )
        assert "(from env MCP_CODER_LLM_PROVIDER)" in active_row
        # The only mention of the variable is that existing row.
        assert self._env_rows(output) == [active_row]
        assert result == 0

    def test_env_unset_adds_no_row(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 3: nothing exported → no extra row."""
        monkeypatch.delenv(self._LABEL, raising=False)
        result, output = self._run(("claude", "default"), capsys)

        assert self._env_rows(output) == []
        assert result == 0


class TestTlsProxySummaryRow:
    """Step 17: a one-line TLS/proxy summary inside the ENVIRONMENT section.

    ``_http.py`` already picks truststore-vs-certifi and notices a proxy, but
    only logs it at DEBUG — invisible on a normal ``verify`` run, which is
    precisely when a corporate-proxy user needs it. Informational only: no
    status symbol, no exit-code impact, and never the proxy URL itself.
    """

    _LABEL = "TLS / proxy"
    _EXC = "mcp_coder.llm.providers.langchain._exceptions"
    _PROXY_VARS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")

    def _clear_proxy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in self._PROXY_VARS:
            monkeypatch.delenv(var, raising=False)

    def _row(self, capsys: pytest.CaptureFixture[str]) -> str:
        _print_environment_section()
        out = capsys.readouterr().out
        return next(line for line in out.splitlines() if self._LABEL in line)

    def test_truststore_available_names_truststore(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 1: truststore importable → the row names truststore."""
        self._clear_proxy(monkeypatch)
        monkeypatch.setattr(f"{self._EXC}._truststore_available", lambda: True)

        assert "SSL context: truststore (OS certificate store)" in self._row(capsys)

    def test_truststore_missing_names_default_context(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 2: no truststore → the row names the default context."""
        self._clear_proxy(monkeypatch)
        monkeypatch.setattr(f"{self._EXC}._truststore_available", lambda: False)

        row = self._row(capsys)
        assert "SSL context: default (certifi/system)" in row
        assert "truststore" not in row

    @pytest.mark.parametrize("var", _PROXY_VARS)
    def test_proxy_reported_without_leaking_the_url(
        self,
        var: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """TDD 3: a set proxy var is reported as a boolean, never as its URL."""
        secret = "http://user:hunter2@proxy.corp.example:8080"
        self._clear_proxy(monkeypatch)
        monkeypatch.setenv(var, secret)

        _print_environment_section()
        out = capsys.readouterr().out

        row = next(line for line in out.splitlines() if self._LABEL in line)
        assert "proxy: configured (HTTPS_PROXY/HTTP_PROXY)" in row
        # The URL — credentials included — must not appear anywhere in stdout.
        assert secret not in out
        assert "hunter2" not in out
        assert "proxy.corp.example" not in out

    def test_no_proxy_env_reports_none(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 4: nothing exported → ``proxy: none``."""
        self._clear_proxy(monkeypatch)

        assert "proxy: none" in self._row(capsys)

    def test_row_carries_no_status_symbol(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 5a: informational row — empty marker slot, aligned like its peers."""
        self._clear_proxy(monkeypatch)

        row = self._row(capsys)
        assert not any(symbol in row for symbol in STATUS_SYMBOLS.values())
        _assert_value_at_column(row, _expected_value_column(2))

    def test_row_uses_the_real_predicates(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The reported context source is whatever ``create_ssl_context`` branches on."""
        from mcp_coder.llm.providers.langchain._exceptions import _truststore_available

        self._clear_proxy(monkeypatch)
        expected = "truststore" if _truststore_available() else "default"

        assert f"SSL context: {expected}" in self._row(capsys)

    def test_row_is_exit_code_neutral(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 5b: a full run still exits 0 whichever way the predicates fall."""
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
        with (
            patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
            patch(f"{_VERIFY}.find_claude_executable", return_value=None),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
            patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok()),
            patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
        ):
            result = execute_verify(_make_args())
        out = capsys.readouterr().out

        assert self._LABEL in out
        assert "proxy.invalid" not in out
        assert result == 0
