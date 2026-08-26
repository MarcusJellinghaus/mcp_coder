"""Tests for resolve_target() — the dialed-URL probe in _config_diagnostics.

Every test stubs ``_create_chat_model`` with a fake chat model exposing
``root_client.base_url`` (openai/azure) or ``base_url`` (ollama), so no
langchain install is required. That stub is also the point of the probe: the
URL must be *read off the constructed client*, never computed from config.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain._config_diagnostics import (
    _NO_BACKEND_TARGET,
    _NOT_CONFIGURED,
    _OLLAMA_DEFAULT_URL,
    _UNSET_TARGET,
    NON_URL_TARGETS,
    ResolvedTarget,
    _targets_match,
    describe_effective_config,
    dialed_url,
    redirect_env_in_effect,
    resolve_target,
)

_PACKAGE = "mcp_coder.llm.providers.langchain"
_CREATE = f"{_PACKAGE}._create_chat_model"
_DIAGNOSTICS = f"{_PACKAGE}._config_diagnostics"

# Everything that can redirect a client, cleared before each test so a
# developer's real environment cannot invent provenance.
_REDIRECT_VARS = (
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
    "AZURE_OPENAI_ENDPOINT",
    "OLLAMA_HOST",
)

_OPENAI_DEFAULT = "https://api.openai.com/v1/"


@pytest.fixture(autouse=True)
def _clear_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _REDIRECT_VARS:
        monkeypatch.delenv(var, raising=False)


class _StubHttpClient:
    """Stand-in for the sync httpx client create_openai_model builds."""

    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class _StubAsyncHttpClient:
    """Stand-in for the async httpx client create_openai_model builds."""

    def __init__(self) -> None:
        self.close_calls = 0

    async def aclose(self) -> None:
        self.close_calls += 1


class _StubRootClient:
    """The openai SDK client hanging off ChatOpenAI.root_client."""

    def __init__(self, base_url: str | None) -> None:
        self.base_url = base_url


class _StubChatModel:
    """Minimal stand-in for a constructed langchain chat model.

    ``via_root_client=True`` reproduces ChatOpenAI / AzureChatOpenAI, which
    expose the dialed URL on ``root_client.base_url``; ``False`` reproduces
    ChatOllama, which exposes ``base_url`` directly and has no httpx clients.
    """

    def __init__(self, url: str | None, *, via_root_client: bool = True) -> None:
        if via_root_client:
            self.root_client = _StubRootClient(url)
            self.http_client = _StubHttpClient()
            self.http_async_client = _StubAsyncHttpClient()
        else:
            self.base_url = url


class _ExplodingChatModel:
    """A constructed client that raises while its URL is being read."""

    def __init__(self) -> None:
        self.http_client = _StubHttpClient()
        self.http_async_client = _StubAsyncHttpClient()

    @property
    def root_client(self) -> Any:
        raise RuntimeError("boom")


def _config(**overrides: str | None) -> dict[str, str | None]:
    """Build a full langchain config dict with *overrides* applied."""
    cfg: dict[str, str | None] = {
        "backend": None,
        "model": None,
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }
    cfg.update(overrides)
    return cfg


def _openai_config(**overrides: str | None) -> dict[str, str | None]:
    return _config(backend="openai", model="gpt-4o", api_key="sk-x", **overrides)


# ---------------------------------------------------------------------------
# dialed_url
# ---------------------------------------------------------------------------


class TestDialedUrl:
    """Tests for dialed_url()."""

    def test_reads_root_client(self) -> None:
        model = _StubChatModel("https://relay.internal/v1")
        assert dialed_url(model) == "https://relay.internal/v1"

    def test_falls_back_to_base_url(self) -> None:
        model = _StubChatModel("http://host:11434", via_root_client=False)
        assert dialed_url(model) == "http://host:11434"

    def test_none_when_no_url_anywhere(self) -> None:
        assert dialed_url(_StubChatModel(None, via_root_client=False)) is None

    def test_stringifies_non_str_url(self) -> None:
        """The openai SDK exposes an httpx.URL, not a str."""

        class _Url:
            def __str__(self) -> str:
                return "https://relay.internal/v1"

        model = _StubChatModel(None)
        model.root_client.base_url = _Url()  # type: ignore[assignment]
        assert dialed_url(model) == "https://relay.internal/v1"


# ---------------------------------------------------------------------------
# _targets_match — shared with step 7
# ---------------------------------------------------------------------------


class TestTargetsMatch:
    """Tests for the provenance predicate."""

    @pytest.mark.parametrize(
        ("candidate", "url"),
        [
            ("https://relay.internal/v1", "https://relay.internal/v1"),
            ("https://relay.internal/v1/", "https://relay.internal/v1"),
            ("https://res.openai.azure.com", "https://res.openai.azure.com/openai/"),
            ("host:11434", "http://host:11434"),
        ],
    )
    def test_match(self, candidate: str, url: str) -> None:
        assert _targets_match(candidate, url)

    @pytest.mark.parametrize(
        ("candidate", "url"),
        [
            ("https://a.internal/v1", "https://b.internal/v1"),
            ("host:11434", "http://otherhost:11434"),
        ],
    )
    def test_no_match(self, candidate: str, url: str) -> None:
        assert not _targets_match(candidate, url)


# ---------------------------------------------------------------------------
# resolve_target
# ---------------------------------------------------------------------------


class TestResolveTargetOpenAI:
    """Tests for the openai backend, where the SDK does the resolving."""

    def test_config_base_url_echoed_by_client(self) -> None:
        """Case 1: config value the client confirms → config is the source."""
        cfg = _openai_config(base_url="https://relay.internal/v1")
        with patch(_CREATE, return_value=_StubChatModel("https://relay.internal/v1")):
            result = resolve_target(cfg)

        assert result == ResolvedTarget(
            url="https://relay.internal/v1",
            source="config.toml [llm.langchain] base_url",
            verified=True,
        )

    def test_env_redirect_named(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Case 2: no config value, OPENAI_BASE_URL is what the client dials."""
        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.internal/v1")
        with patch(_CREATE, return_value=_StubChatModel("https://relay.internal/v1")):
            result = resolve_target(_openai_config())

        assert result.url == "https://relay.internal/v1"
        assert result.source == "OPENAI_BASE_URL env var"
        assert result.verified is True

    def test_two_redirects_different_values_value_match_wins(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 2b: the variable named is the one whose value the client used."""
        monkeypatch.setenv("OPENAI_API_BASE", "https://a.internal/v1")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://b.internal/v1")
        with patch(_CREATE, return_value=_StubChatModel("https://b.internal/v1")):
            result = resolve_target(_openai_config())

        assert result.url == "https://b.internal/v1"
        assert result.source == "OPENAI_BASE_URL env var"

    def test_two_redirects_same_value_precedence_wins(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 2c: value match cannot discriminate → tuple order decides."""
        monkeypatch.setenv("OPENAI_API_BASE", "https://relay.internal/v1")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.internal/v1")
        with patch(_CREATE, return_value=_StubChatModel("https://relay.internal/v1")):
            result = resolve_target(_openai_config())

        assert result.source == "OPENAI_API_BASE env var"

    def test_nothing_set_is_sdk_default(self) -> None:
        """Case 3: no config, no redirect → the SDK's own default."""
        with patch(_CREATE, return_value=_StubChatModel(_OPENAI_DEFAULT)):
            result = resolve_target(_openai_config())

        assert result == ResolvedTarget(
            url=_OPENAI_DEFAULT, source="SDK default", verified=True
        )

    def test_stale_azure_endpoint_is_inert(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 3b: AZURE_OPENAI_ENDPOINT never applies outside Azure mode."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://res.openai.azure.com")
        cfg = _openai_config()
        with patch(_CREATE, return_value=_StubChatModel(_OPENAI_DEFAULT)):
            result = resolve_target(cfg)

        assert result.source == "SDK default"
        assert redirect_env_in_effect(cfg, result.url) is None

    def test_azure_endpoint_named_in_azure_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 3c: in Azure mode the client dials a path under the resource."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://res.openai.azure.com")
        cfg = _openai_config(api_version="2024-02-01")
        dialed = "https://res.openai.azure.com/openai/deployments/dep/"
        with patch(_CREATE, return_value=_StubChatModel(dialed)):
            result = resolve_target(cfg)

        assert result.url == dialed
        assert result.source == "AZURE_OPENAI_ENDPOINT env var"

    def test_construction_failure_with_config_value(self) -> None:
        """Case 4: fall back to config, clearly labelled unverified."""
        cfg = _openai_config(base_url="https://relay.internal/v1")
        with patch(_CREATE, side_effect=ValueError("no api_key")):
            result = resolve_target(cfg)

        assert result.url == "https://relay.internal/v1"
        assert result.verified is False
        assert "config.toml" in result.source
        assert "unverified" in result.source

    def test_construction_failure_without_config_value(self) -> None:
        """Case 4b: nothing supplied a value → never claim config.toml did."""
        with patch(_CREATE, side_effect=ValueError("no api_key")):
            result = resolve_target(_openai_config())

        assert result.url == _UNSET_TARGET
        assert result.verified is False
        assert "unverified" in result.source
        assert "config.toml" not in result.source

    def test_http_clients_closed_once(self) -> None:
        """Case 6: the probe owns both httpx clients and must release them."""
        model = _StubChatModel(_OPENAI_DEFAULT)
        with patch(_CREATE, return_value=model):
            resolve_target(_openai_config())

        assert model.http_client.close_calls == 1
        assert model.http_async_client.close_calls == 1

    def test_http_clients_closed_when_inspection_fails(self) -> None:
        """A client that explodes on read is still released."""
        model = _ExplodingChatModel()
        with patch(_CREATE, return_value=model):
            with pytest.raises(RuntimeError):
                resolve_target(_openai_config())

        assert model.http_client.close_calls == 1
        assert model.http_async_client.close_calls == 1


class TestResolveTargetNoTarget:
    """Backends with nothing to dial, and backends that do not exist."""

    @pytest.mark.parametrize("backend", ["gemini", "anthropic"])
    def test_backend_without_target(self, backend: str) -> None:
        """Case 5: no client is constructed at all."""
        with patch(_CREATE) as create:
            result = resolve_target(_config(backend=backend, model="m", api_key="k"))

        create.assert_not_called()
        assert result.url == "n/a"
        assert result.verified is True

    @pytest.mark.parametrize("backend", [None, "opnai", "azure"])
    def test_unset_or_typod_backend(self, backend: str | None) -> None:
        """Case 5b: an unscoped backend is not 'a backend with no target'."""
        with patch(_CREATE) as create:
            result = resolve_target(_config(backend=backend, model="m"))

        create.assert_not_called()
        assert result.url == _NO_BACKEND_TARGET
        assert result.verified is False
        assert result.source == "no supported backend configured"
        assert "no configurable target" not in result.source


class TestResolveTargetOllama:
    """Tests for ollama, where our own code does the resolving."""

    def test_config_base_url(self) -> None:
        cfg = _config(backend="ollama", model="llama3", base_url="http://box:11434")
        model = _StubChatModel("http://box:11434", via_root_client=False)
        with patch(_CREATE, return_value=model):
            result = resolve_target(cfg)

        assert result.url == "http://box:11434"
        assert result.source == "config.toml [llm.langchain] base_url"

    def test_ollama_host_named(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Case 7: OLLAMA_HOST outranks config and is reported as the source."""
        monkeypatch.setenv("OLLAMA_HOST", "box:11434")
        cfg = _config(backend="ollama", model="llama3")
        model = _StubChatModel("http://box:11434", via_root_client=False)
        with patch(_CREATE, return_value=model):
            result = resolve_target(cfg)

        assert result.url == "http://box:11434"
        assert result.source == "OLLAMA_HOST env var"

    def test_bare_default_is_never_unknown(self) -> None:
        """Case 7b: the most common ollama setup reports no URL at all."""
        cfg = _config(backend="ollama", model="llama3")
        model = _StubChatModel(None, via_root_client=False)
        with patch(_CREATE, return_value=model):
            result = resolve_target(cfg)

        assert result.url == _OLLAMA_DEFAULT_URL
        assert result.source == "SDK default"
        assert result.verified is True
        assert "unknown" not in result.url


class TestNotConfiguredSentinelIsShared:
    """The echo renders the same literal the shape check skips on."""

    def test_echo_sentinel_is_the_unresolved_target_sentinel(self) -> None:
        assert _NOT_CONFIGURED is _UNSET_TARGET
        assert _NOT_CONFIGURED in NON_URL_TARGETS


class TestImportCycle:
    """Case 8: regression guard for the deferred _create_chat_model import."""

    def test_package_imports_from_scratch(self) -> None:
        prefix = _PACKAGE + "."
        saved = {
            name: module
            for name, module in sys.modules.items()
            if name == _PACKAGE or name.startswith(prefix)
        }
        for name in saved:
            del sys.modules[name]
        try:
            package = importlib.import_module(_PACKAGE)
            assert package.validate is not None
        finally:
            for name in [
                n for n in list(sys.modules) if n == _PACKAGE or n.startswith(prefix)
            ]:
                del sys.modules[name]
            sys.modules.update(saved)


class TestAsyncCloseIsAwaited:
    """The async client must actually be awaited, not merely referenced."""

    def test_aclose_coroutine_is_run(self) -> None:
        model = _StubChatModel(_OPENAI_DEFAULT)
        with patch(_CREATE, return_value=model):
            resolve_target(_openai_config())

        # A coroutine that was created but never awaited would leave the
        # counter at zero and emit a RuntimeWarning.
        assert model.http_async_client.close_calls == 1
        assert asyncio.iscoroutinefunction(model.http_async_client.aclose)


# ---------------------------------------------------------------------------
# describe_effective_config — pure formatting over an already-resolved target
# ---------------------------------------------------------------------------

_SDK_DEFAULT_TARGET = ResolvedTarget(_OPENAI_DEFAULT, "SDK default", True)
_NO_TARGET = ResolvedTarget("n/a", "backend has no configurable target", True)


def _rows(
    config: dict[str, str | None],
    target: ResolvedTarget = _SDK_DEFAULT_TARGET,
    **kwargs: Any,
) -> dict[str, str]:
    """Return describe_effective_config's rows keyed by label."""
    return dict(describe_effective_config(config, target, **kwargs))


class TestDescribeEffectiveConfigRows:
    """Case 1: five rows in a stable order, naming the real discriminator."""

    def test_row_order_is_stable(self) -> None:
        rows = describe_effective_config(_openai_config(), _SDK_DEFAULT_TARGET)
        assert [label for label, _value in rows] == [
            "backend",
            "mode",
            "model",
            "base_url",
            "api_key",
        ]

    def test_plain_openai_names_api_version_as_discriminator(self) -> None:
        assert _rows(_openai_config())["mode"] == "plain openai (api_version not set)"

    def test_azure_names_api_version_as_discriminator(self) -> None:
        rows = _rows(_openai_config(api_version="2024-02-01"))
        assert rows["mode"] == "Azure OpenAI (api_version set)"

    @pytest.mark.parametrize("backend", [None, "opnai"])
    def test_no_mode_claimed_without_a_usable_backend(
        self, backend: str | None
    ) -> None:
        """A backend that mode_of() rejects has no mode to name."""
        rows = _rows(_config(backend=backend, model="m"), _NO_TARGET)

        assert rows["mode"] == "(not applicable — backend not configured)"
        assert "None" not in rows["mode"]

    def test_unset_backend_row_matches_the_mode_row(self) -> None:
        assert _rows(_config(), _NO_TARGET)["backend"] == "(not configured)"

    def test_typod_backend_row_shows_what_was_configured(self) -> None:
        assert _rows(_config(backend="opnai"), _NO_TARGET)["backend"] == "opnai"

    def test_stray_api_version_is_named_not_denied(self) -> None:
        """A gemini config with api_version takes the non-Azure branch anyway.

        Claiming 'api_version not set' here would contradict the contract
        finding that the key is ignored by this backend.
        """
        rows = _rows(_config(backend="gemini", model="m", api_version="2024-02-01"))

        assert rows["mode"] == "plain gemini (api_version ignored by gemini)"
        assert "not set" not in rows["mode"]

    def test_unset_model(self) -> None:
        assert _rows(_config(backend="openai"))["model"] == "(not configured)"


class TestDescribeEffectiveConfigBaseUrl:
    """Case 2/3: the base_url row echoes the passed target, and only that."""

    def test_source_carried_verbatim(self) -> None:
        target = ResolvedTarget(
            "https://relay.internal/v1", "config.toml [llm.langchain] base_url", True
        )
        rows = _rows(_openai_config(base_url="https://relay.internal/v1"), target)

        assert (
            rows["base_url"]
            == "https://relay.internal/v1   (config.toml [llm.langchain] base_url)"
        )

    def test_unverified_wording_preserved(self) -> None:
        target = ResolvedTarget(
            "https://relay.internal/v1",
            "config.toml (unverified — client not constructed)",
            False,
        )

        assert "unverified" in _rows(_openai_config(), target)["base_url"]

    def test_builder_never_resolves_the_target(self) -> None:
        """Case 2: the caller owns the single resolve_target() call."""
        with patch(f"{_DIAGNOSTICS}.resolve_target") as resolve:
            describe_effective_config(_openai_config(), _SDK_DEFAULT_TARGET)

        resolve.assert_not_called()

    def test_backend_without_target(self) -> None:
        """Case 3: gemini has nothing to dial."""
        rows = _rows(_config(backend="gemini", model="m"), _NO_TARGET)

        assert rows["base_url"] == "n/a   (backend has no configurable target)"


class TestDescribeEffectiveConfigApiKey:
    """Case 3b: the api_key row shows the *resolved* key under its own label."""

    def test_masked_value_and_override_text(self) -> None:
        cfg = _config(
            backend="openai", model="gpt-4o", api_key="sk-configured-and-beaten"
        )
        rows = _rows(
            cfg,
            api_key_masked="Qwen...abcd",
            api_key_source="OPENAI_API_KEY env var",
            api_key_overridden=True,
        )

        assert rows["api_key"] == (
            "Qwen...abcd   (from OPENAI_API_KEY env var "
            "— overrides config.toml api_key)"
        )
        # The losing config value must never surface under the winner's label.
        assert "sk-configured-and-beaten" not in "\n".join(rows.values())

    def test_no_override_text_when_config_won(self) -> None:
        rows = _rows(
            _openai_config(),
            api_key_masked="sk-a...5678",
            api_key_source="config.toml",
        )

        assert rows["api_key"] == "sk-a...5678   (from config.toml)"
        assert "overrides" not in rows["api_key"]

    def test_source_without_readable_value(self) -> None:
        """Gemini's keyless Vertex carve-out satisfies the credential."""
        rows = _rows(
            _config(backend="gemini", model="m"),
            _NO_TARGET,
            api_key_source="GOOGLE_GENAI_USE_VERTEXAI env var",
        )

        assert rows["api_key"] == (
            "(not set — satisfied via GOOGLE_GENAI_USE_VERTEXAI env var)"
        )

    def test_bare_not_set_needs_both_none(self) -> None:
        """Config carries an api_key; the builder must not read it."""
        assert _rows(_openai_config())["api_key"] == "(not set)"
