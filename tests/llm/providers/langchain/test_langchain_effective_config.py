"""Tests for the effective-config echo and the provenance it reports.

Covers ``_resolve_api_key`` (mode-keyed, 3-tuple) and the ``verify_langchain``
wiring that turns it — plus the single ``resolve_target()`` call of the run —
into ``result["effective_config"]`` and the two exit-neutral flag rows.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain._config_diagnostics import (
    ResolvedTarget,
    describe_effective_config,
)
from mcp_coder.llm.providers.langchain.verification import (
    _resolve_api_key,
    verify_langchain,
)

_VERIFICATION = "mcp_coder.llm.providers.langchain.verification"
_MODELS = "mcp_coder.llm.providers.langchain._models"

# Every variable that can supply a credential or redirect a client, cleared
# before each test so a developer's real environment cannot invent provenance.
_SENSITIVE_VARS = (
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_AD_TOKEN",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "ANTHROPIC_API_KEY",
    "OLLAMA_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
    "AZURE_OPENAI_ENDPOINT",
    "OLLAMA_HOST",
)

_OPENAI_DEFAULT = "https://api.openai.com/v1/"
_SDK_DEFAULT_TARGET = ResolvedTarget(_OPENAI_DEFAULT, "SDK default", True)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _SENSITIVE_VARS:
        monkeypatch.delenv(var, raising=False)


def _config(**overrides: str | None) -> dict[str, str | None]:
    """Build a full langchain config dict with *overrides* applied."""
    cfg: dict[str, str | None] = {
        "provider": "langchain",
        "backend": None,
        "model": None,
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }
    cfg.update(overrides)
    return cfg


def _openai_config(**overrides: str | None) -> dict[str, str | None]:
    return _config(backend="openai", model="gpt-4o", **overrides)


def _run_verify(
    config: dict[str, str | None],
    target: ResolvedTarget = _SDK_DEFAULT_TARGET,
) -> tuple[dict[str, Any], MagicMock]:
    """Run verify_langchain against *config*, stubbing the target probe.

    Returns the result dict and the ``resolve_target`` mock, so callers can
    assert on the number of probes as well as on the rows.
    """
    with (
        patch(f"{_VERIFICATION}._load_langchain_config", return_value=config),
        patch(f"{_VERIFICATION}._check_package_installed", return_value=True),
        patch(f"{_VERIFICATION}.resolve_target", return_value=target) as resolve,
    ):
        result = verify_langchain()
    return result, resolve


# ---------------------------------------------------------------------------
# _resolve_api_key — keyed by mode, resolving in the client's order
# ---------------------------------------------------------------------------


class TestResolveApiKeyPrimary:
    """The one variable our own create_*_model reads, and it beats config."""

    def test_primary_env_var_beats_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")

        assert _resolve_api_key("openai", "config-key") == (
            "env-key",
            "OPENAI_API_KEY env var",
            True,
        )

    def test_primary_env_var_filling_a_gap_is_not_an_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")

        assert _resolve_api_key("openai", None) == (
            "env-key",
            "OPENAI_API_KEY env var",
            False,
        )

    def test_falls_back_to_config(self) -> None:
        assert _resolve_api_key("openai", "config-key") == (
            "config-key",
            "config.toml",
            False,
        )

    def test_no_key_available(self) -> None:
        assert _resolve_api_key("openai", None) == (None, None, False)

    @pytest.mark.parametrize(
        ("mode", "var"),
        [
            ("gemini", "GEMINI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("ollama", "OLLAMA_API_KEY"),
            ("azure", "OPENAI_API_KEY"),
        ],
    )
    def test_primary_var_per_mode(
        self, mode: str, var: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(var, "the-key")

        assert _resolve_api_key(mode, None) == ("the-key", f"{var} env var", False)

    def test_unknown_mode_still_reads_config(self) -> None:
        assert _resolve_api_key(None, "config-key") == (
            "config-key",
            "config.toml",
            False,
        )

    def test_unknown_mode_without_config(self) -> None:
        assert _resolve_api_key(None, None) == (None, None, False)


class TestResolveApiKeySecondary:
    """Case 3c: SDK fallbacks the contract accepts must be named, not denied."""

    @pytest.mark.parametrize(
        ("mode", "var"),
        [
            ("azure", "AZURE_OPENAI_API_KEY"),
            ("azure", "AZURE_OPENAI_AD_TOKEN"),
            ("gemini", "GOOGLE_API_KEY"),
        ],
    )
    def test_secondary_var_named_as_the_source(
        self, mode: str, var: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(var, "the-key")
        key, source, overridden = _resolve_api_key(mode, None)

        assert (key, source, overridden) == ("the-key", f"{var} env var", False)

        # ...and the echo row names it rather than rendering "(not set)".
        rows = dict(
            describe_effective_config(
                _openai_config(api_version="2024-02-01"),
                _SDK_DEFAULT_TARGET,
                api_key_masked="the-...-key",
                api_key_source=source,
            )
        )
        assert rows["api_key"] == f"the-...-key   (from {var} env var)"

    def test_keyless_carve_out_reports_a_source_without_a_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "1")

        assert _resolve_api_key("gemini", None) == (
            None,
            "GOOGLE_GENAI_USE_VERTEXAI env var",
            False,
        )

    def test_nothing_set_at_all(self) -> None:
        assert _resolve_api_key("azure", None) == (None, None, False)

    @pytest.mark.parametrize(
        ("mode", "var"),
        [("azure", "AZURE_OPENAI_API_KEY"), ("gemini", "GOOGLE_API_KEY")],
    )
    def test_config_key_beats_a_secondary_var(
        self, mode: str, var: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 3d: SDK fallbacks apply only when no key is passed at all."""
        monkeypatch.setenv(var, "sdk-fallback-key")

        assert _resolve_api_key(mode, "config-key") == (
            "config-key",
            "config.toml",
            False,
        )

    def test_primary_still_beats_config_in_azure_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "sdk-fallback-key")

        assert _resolve_api_key("azure", "config-key") == (
            "env-key",
            "OPENAI_API_KEY env var",
            True,
        )


# ---------------------------------------------------------------------------
# verify_langchain wiring
# ---------------------------------------------------------------------------


class TestEffectiveConfigWiring:
    """Case 4: one probe per run, rows carried as a list."""

    def test_resolve_target_called_exactly_once(self) -> None:
        _result, resolve = _run_verify(_openai_config(api_key="sk-abcd1234wxyz5678"))

        resolve.assert_called_once()

    def test_effective_config_is_a_list_of_pairs(self) -> None:
        result, _resolve = _run_verify(_openai_config(api_key="sk-abcd1234wxyz5678"))
        rows = result["effective_config"]

        assert isinstance(rows, list)
        assert [label for label, _value in rows] == [
            "backend",
            "mode",
            "model",
            "base_url",
            "api_key",
        ]

    def test_echo_shows_the_resolved_key_not_the_config_one(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env-12345678")
        result, _resolve = _run_verify(_openai_config(api_key="sk-abcd1234wxyz5678"))
        rows = dict(result["effective_config"])

        assert rows["api_key"].startswith("sk-f...5678")
        assert "OPENAI_API_KEY env var" in rows["api_key"]
        assert "sk-a...5678" not in rows["api_key"]

    def test_echo_carries_the_probed_target(self) -> None:
        target = ResolvedTarget(
            "https://relay.internal/v1", "OPENAI_BASE_URL env var", True
        )
        result, _resolve = _run_verify(_openai_config(), target)
        rows = dict(result["effective_config"])

        assert rows["base_url"] == (
            "https://relay.internal/v1   (OPENAI_BASE_URL env var)"
        )


class TestBaseUrlRedirectRow:
    """Case 6/6b: the row names the variable that actually produced the URL."""

    def test_row_added_when_env_var_supplied_the_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.internal/v1")
        target = ResolvedTarget(
            "https://relay.internal/v1", "OPENAI_BASE_URL env var", True
        )
        # A key is supplied so the contract is satisfied: the assertion below
        # is that the *redirect* row is exit-neutral, not that the config is.
        result, _resolve = _run_verify(
            _openai_config(api_key="sk-abcd1234wxyz5678"), target
        )
        row = result["base_url_redirect"]

        assert row["ok"] is None
        assert row["value"] == (
            "OPENAI_BASE_URL is set — requests go to https://relay.internal/v1 "
            "(no base_url in config.toml)"
        )
        assert result["overall_ok"] is True

    def test_row_claims_an_override_only_when_config_named_a_target(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ollama is the one backend where env genuinely beats config."""
        monkeypatch.setenv("OLLAMA_HOST", "http://box:11434")
        target = ResolvedTarget("http://box:11434", "OLLAMA_HOST env var", True)
        with (
            patch(
                f"{_MODELS}._check_ollama_daemon",
                return_value={"ok": True, "value": "up"},
            ),
            patch(
                f"{_MODELS}.check_ollama_tool_capability",
                return_value={"ok": True, "value": "tools"},
            ),
        ):
            result, _resolve = _run_verify(
                _config(
                    backend="ollama",
                    model="llama3",
                    base_url="http://configured:11434",
                ),
                target,
            )

        assert result["base_url_redirect"]["value"] == (
            "OLLAMA_HOST overrides config.toml — requests go to http://box:11434"
        )

    def test_no_row_without_a_redirect_variable(self) -> None:
        result, _resolve = _run_verify(_openai_config())

        assert "base_url_redirect" not in result

    def test_no_row_when_config_implied_the_same_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nothing was redirected: config and the variable agree."""
        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.internal/v1")
        target = ResolvedTarget(
            "https://relay.internal/v1", "config.toml [llm.langchain] base_url", True
        )
        result, _resolve = _run_verify(
            _openai_config(base_url="https://relay.internal/v1"), target
        )

        assert "base_url_redirect" not in result

    def test_stale_azure_endpoint_is_inert(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 6b: AZURE_OPENAI_ENDPOINT cannot apply to a plain openai config."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://res.openai.azure.com")
        result, _resolve = _run_verify(_openai_config())
        rows = dict(result["effective_config"])

        assert "base_url_redirect" not in result
        assert rows["base_url"].endswith("(SDK default)")

    def test_only_the_matching_variable_is_named(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 6b: OPENAI_BASE_URL lost, so it must not be reported."""
        monkeypatch.setenv("OPENAI_API_BASE", "https://a.internal/v1")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://b.internal/v1")
        target = ResolvedTarget(
            "https://a.internal/v1", "OPENAI_API_BASE env var", True
        )
        result, _resolve = _run_verify(_openai_config(), target)
        value = result["base_url_redirect"]["value"]

        assert value.count("OPENAI_API_BASE") == 1
        assert "OPENAI_BASE_URL" not in value


class TestApiKeyOverrideRow:
    """Case 7: flag an env var that beat a configured api_key."""

    def _override_row(
        self, monkeypatch: pytest.MonkeyPatch, target: ResolvedTarget
    ) -> dict[str, Any]:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env-12345678")
        result, _resolve = _run_verify(
            _openai_config(api_key="sk-abcd1234wxyz5678"), target
        )
        assert result["overall_ok"] is True
        return dict(result)

    def test_row_names_the_api_key_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = self._override_row(monkeypatch, _SDK_DEFAULT_TARGET)
        row = result["api_key_override"]

        assert row["ok"] is None
        assert row["value"] == (
            "OPENAI_API_KEY env var overrides [llm.langchain] api_key in config.toml"
        )

    def test_row_text_ignores_base_url_redirection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The row is built from key_source, never from the redirect variable."""
        plain = self._override_row(monkeypatch, _SDK_DEFAULT_TARGET)
        without = plain["api_key_override"]["value"]

        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.internal/v1")
        redirected = ResolvedTarget(
            "https://relay.internal/v1", "OPENAI_BASE_URL env var", True
        )
        result = self._override_row(monkeypatch, redirected)

        assert "base_url_redirect" in result  # the redirect really is in effect
        value = result["api_key_override"]["value"]
        assert value == without
        assert "OPENAI_BASE_URL" not in value
        assert "None" not in value

    def test_no_row_when_env_var_filled_a_gap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env-12345678")
        result, _resolve = _run_verify(_openai_config())
        rows = dict(result["effective_config"])

        assert "api_key_override" not in result
        assert "overrides" not in rows["api_key"]

    def test_no_row_when_only_a_secondary_var_is_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 3d: the config key won, so nothing overrode it."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "sdk-fallback-key")
        result, _resolve = _run_verify(
            _openai_config(api_key="sk-abcd1234wxyz5678", api_version="2024-02-01")
        )
        rows = dict(result["effective_config"])

        assert "api_key_override" not in result
        assert rows["api_key"] == "sk-a...5678   (from config.toml)"
