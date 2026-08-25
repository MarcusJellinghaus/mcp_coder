"""Tests for the base-URL shape heuristic, rebased on the resolved target.

The check no longer inspects the raw config string: it inspects the URL the
constructed client will actually dial, so a redirect via ``OPENAI_BASE_URL``
or ``OPENAI_API_BASE`` is shape-checked too — a case the config-string version
was silent about.

The ``verify_langchain`` wiring tests stub ``_create_chat_model`` so the real
:func:`resolve_target` runs end to end without a langchain install.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify_formatting import _LABEL_MAP
from mcp_coder.llm.providers.langchain._config_diagnostics import (
    _UNSET_TARGET,
    ResolvedTarget,
)
from mcp_coder.llm.providers.langchain.verification import (
    _check_base_url_shape,
    verify_langchain,
)

_PACKAGE = "mcp_coder.llm.providers.langchain"
_CREATE = f"{_PACKAGE}._create_chat_model"
_VERIFICATION = f"{_PACKAGE}.verification"
_MODELS = f"{_PACKAGE}._models"

# Everything that can redirect a client or supply a credential, cleared before
# each test so a developer's real environment cannot invent provenance.
_SENSITIVE_VARS = (
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_AD_TOKEN",
    "OLLAMA_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
    "AZURE_OPENAI_ENDPOINT",
    "OLLAMA_HOST",
)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _SENSITIVE_VARS:
        monkeypatch.delenv(var, raising=False)


class _StubRootClient:
    """The openai SDK client hanging off ChatOpenAI.root_client."""

    def __init__(self, base_url: str | None) -> None:
        self.base_url = base_url


class _StubChatModel:
    """Minimal stand-in for a constructed langchain chat model."""

    def __init__(self, url: str | None, *, via_root_client: bool = True) -> None:
        if via_root_client:
            self.root_client = _StubRootClient(url)
        else:
            self.base_url = url


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
    defaults: dict[str, str | None] = {
        "backend": "openai",
        "model": "gpt-4o",
        "api_key": "sk-x",
    }
    defaults.update(overrides)
    return _config(**defaults)


def _target(url: str, source: str = "SDK default") -> ResolvedTarget:
    return ResolvedTarget(url, source, True)


# ---------------------------------------------------------------------------
# _check_base_url_shape — the three heuristics, now over the dialed URL
# ---------------------------------------------------------------------------


class TestCheckBaseUrlShapeHeuristics:
    """The heuristics themselves are unchanged; only the input is."""

    def test_completions_in_path_warns(self) -> None:
        result = _check_base_url_shape(_target("https://h/v1/completions"), None)
        assert result is not None
        assert result["ok"] is None
        assert "/completions" in result["value"]

    def test_chat_completions_in_path_warns(self) -> None:
        result = _check_base_url_shape(_target("https://h/v1/chat/completions"), None)
        assert result is not None
        assert result["ok"] is None
        assert "/completions" in result["value"]

    def test_no_scheme_is_malformed(self) -> None:
        result = _check_base_url_shape(_target("host/v1"), None)
        assert result is not None
        assert result["ok"] is None
        assert "malformed" in result["value"]

    def test_no_host_is_malformed(self) -> None:
        result = _check_base_url_shape(_target("https:///v1"), None)
        assert result is not None
        assert result["ok"] is None
        assert "malformed" in result["value"]

    def test_valid_without_v1_is_info(self) -> None:
        result = _check_base_url_shape(_target("https://h/openai"), None)
        assert result is not None
        assert result["ok"] is True
        assert "most relays use .../v1" in result["value"]

    def test_healthy_v1_base_url(self) -> None:
        result = _check_base_url_shape(_target("https://h/v1"), None)
        assert result is not None
        assert result["ok"] is True
        assert result["value"].startswith("https://h/v1 ")
        assert "most relays" not in result["value"]

    def test_healthy_v1_base_url_trailing_slash(self) -> None:
        """TDD 5b: rstrip('/') leaves it ending in /v1, so it is the OK branch."""
        result = _check_base_url_shape(_target("https://api.openai.com/v1/"), None)
        assert result is not None
        assert result["ok"] is True
        assert "most relays use .../v1" not in result["value"]


class TestCheckBaseUrlShapeProvenance:
    """TDD 5: every returned value names where the URL came from."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://h/v1/completions",  # warn — /completions
            "host/v1",  # warn — malformed
            "https://h/openai",  # ok — no /v1 suffix
            "https://h/v1",  # ok — healthy
        ],
    )
    def test_all_branches_carry_the_source(self, url: str) -> None:
        result = _check_base_url_shape(_target(url, "OPENAI_BASE_URL env var"), None)
        assert result is not None
        assert result["value"].endswith("(source: OPENAI_BASE_URL env var)")

    @pytest.mark.parametrize(
        "url",
        [
            "https://h/v1/completions",
            "host/v1",
            "https://h/openai",
            "https://h/v1",
        ],
    )
    def test_never_reports_failure(self, url: str) -> None:
        """TDD 6: the check is advisory — ok is True or None, never False."""
        result = _check_base_url_shape(_target(url), None)
        assert result is not None
        assert result["ok"] in (True, None)


class TestCheckBaseUrlShapeSkips:
    """Cases where the heuristic must stay silent."""

    def test_api_version_set_skips(self) -> None:
        """TDD 3: Azure's dialed URL legitimately has no /v1 suffix."""
        azure_url = "https://res.openai.azure.com/openai/deployments/gpt-4o/"
        assert _check_base_url_shape(_target(azure_url), "2024-02-01") is None

    def test_na_target_skips(self) -> None:
        """TDD 4: gemini/anthropic have no configurable target."""
        assert (
            _check_base_url_shape(
                ResolvedTarget("n/a", "backend has no configurable target", True), None
            )
            is None
        )

    def test_unset_sentinel_skips(self) -> None:
        """TDD 4b: the unverified sentinel is not a URL and must not be judged."""
        assert (
            _check_base_url_shape(
                ResolvedTarget(
                    _UNSET_TARGET, "unverified — client not constructed", False
                ),
                None,
            )
            is None
        )

    def test_unverified_config_value_is_still_checked(self) -> None:
        """TDD 4b: only the sentinel suppresses; a real config value is checked."""
        result = _check_base_url_shape(
            ResolvedTarget(
                "https://relay.internal/v1/completions",
                "config.toml (unverified — client not constructed)",
                False,
            ),
            None,
        )
        assert result is not None
        assert result["ok"] is None
        assert "/completions" in result["value"]


# ---------------------------------------------------------------------------
# verify_langchain wiring
# ---------------------------------------------------------------------------


def _run_verify(
    config: dict[str, str | None],
    chat_model: Any = None,
    create_side_effect: Exception | None = None,
) -> dict[str, Any]:
    """Run verify_langchain with the real resolve_target over a stub client."""
    create_kwargs: dict[str, Any] = (
        {"side_effect": create_side_effect}
        if create_side_effect is not None
        else {"return_value": chat_model}
    )
    with (
        patch(f"{_VERIFICATION}._load_langchain_config", return_value=config),
        patch(f"{_VERIFICATION}._check_package_installed", return_value=True),
        patch(_CREATE, **create_kwargs),
    ):
        return verify_langchain()


class TestVerifyLangchainBaseUrlShape:
    """The row verify_langchain builds from the resolved target."""

    def test_env_redirect_to_malformed_url_now_fires(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TDD 1: config base_url unset — previously silent, now checked."""
        monkeypatch.setenv("OPENAI_BASE_URL", "relay.internal/v1")
        result = _run_verify(
            _openai_config(), chat_model=_StubChatModel("relay.internal/v1")
        )
        row = result["base_url_shape"]
        assert row["ok"] is None
        assert "malformed" in row["value"]
        assert row["value"].endswith("(source: OPENAI_BASE_URL env var)")

    def test_env_redirect_names_the_variable_as_source(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TDD 2: OPENAI_API_BASE redirect is heuristic-checked and attributed."""
        monkeypatch.setenv("OPENAI_API_BASE", "https://relay.internal/openai")
        result = _run_verify(
            _openai_config(),
            chat_model=_StubChatModel("https://relay.internal/openai"),
        )
        row = result["base_url_shape"]
        assert row["ok"] is True
        assert "most relays use .../v1" in row["value"]
        assert row["value"].endswith("(source: OPENAI_API_BASE env var)")

    def test_bad_shape_does_not_change_overall_ok(self) -> None:
        """TDD 6: a warning row never flips the exit-driving flag."""
        result = _run_verify(
            _openai_config(base_url="https://h/v1/completions"),
            chat_model=_StubChatModel("https://h/v1/completions"),
        )
        assert result["base_url_shape"]["ok"] is None
        assert result["overall_ok"] is True

    def test_azure_config_has_no_shape_row(self) -> None:
        """TDD 3: the Azure skip survives the rebase, at the wiring level."""
        azure_url = "https://res.openai.azure.com/openai/deployments/gpt-4o/"
        result = _run_verify(
            _openai_config(
                base_url="https://res.openai.azure.com", api_version="2024-02-01"
            ),
            chat_model=_StubChatModel(azure_url),
        )
        assert "base_url_shape" not in result

    def test_unconstructible_client_without_config_has_no_row(self) -> None:
        """TDD 4b: the '(not configured)' sentinel is never called malformed."""
        result = _run_verify(
            _openai_config(api_key=None),
            create_side_effect=ValueError("api_key is required"),
        )
        assert "base_url_shape" not in result

    def test_unconstructible_client_with_config_still_checks(self) -> None:
        """TDD 4b: a configured base_url is checked even when unverified."""
        result = _run_verify(
            _openai_config(api_key=None, base_url="https://h/v1/chat/completions"),
            create_side_effect=ValueError("api_key is required"),
        )
        row = result["base_url_shape"]
        assert row["ok"] is None
        assert "/completions" in row["value"]
        assert "(source: config.toml (unverified" in row["value"]

    def test_ollama_host_redirect_has_no_shape_row(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TDD 7: the gate stays at openai — the redirect row reports OLLAMA_HOST."""
        monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
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
            result = _run_verify(
                _config(backend="ollama", model="llama3"),
                chat_model=_StubChatModel(
                    "http://localhost:11434", via_root_client=False
                ),
            )
        assert "base_url_shape" not in result
        assert result["base_url_redirect"]["value"].startswith("OLLAMA_HOST")

    def test_target_is_resolved_exactly_once(self) -> None:
        """TDD 8: one probe per run, shared by the echo and the shape check."""
        probe = MagicMock(return_value=_target("https://h/openai"))
        with (
            patch(
                f"{_VERIFICATION}._load_langchain_config", return_value=_openai_config()
            ),
            patch(f"{_VERIFICATION}._check_package_installed", return_value=True),
            patch(f"{_VERIFICATION}.resolve_target", probe),
        ):
            result = verify_langchain()
        assert probe.call_count == 1
        assert "base_url_shape" in result
        assert result["effective_config"]


class TestBaseUrlShapeLabel:
    """TDD 9: the result key and its label carry the new vocabulary."""

    def test_label_map_entry(self) -> None:
        assert _LABEL_MAP["base_url_shape"] == "Base URL"

    def test_no_endpoint_vocabulary_left(self) -> None:
        assert "endpoint_shape" not in _LABEL_MAP
        assert "Endpoint" not in _LABEL_MAP.values()
