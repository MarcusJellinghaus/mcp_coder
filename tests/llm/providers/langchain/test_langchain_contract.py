"""Tests for the per-backend configuration contract (_config_diagnostics).

Table-driven: one test per contract cell plus the two conditional rules
(Azure's ``base_url`` and the mode-keyed ``api_key`` env lookup).

Several tests also construct the real backend model to guard the SDK facts the
contract table rests on. Those assertions only bite when the ``langchain``
extras are installed; without them the backend modules are ``MagicMock``s (see
``conftest.py``) and the construction trivially succeeds.
"""

from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain._config_diagnostics import (
    Finding,
    mode_of,
    validate,
)

# Every variable that can satisfy a credential rule, cleared before each test
# so a developer's real environment cannot mask a missing-key finding.
_CREDENTIAL_VARS = (
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_AD_TOKEN",
    "AZURE_OPENAI_ENDPOINT",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "ANTHROPIC_API_KEY",
    "OLLAMA_API_KEY",
)


@pytest.fixture(autouse=True)
def _clear_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every credential/endpoint variable the contract consults."""
    for var in _CREDENTIAL_VARS:
        monkeypatch.delenv(var, raising=False)


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


def _by_key(findings: list[Finding]) -> dict[str, Finding]:
    """Index findings by the config field they are about."""
    return {f["key"]: f for f in findings}


# ---------------------------------------------------------------------------
# mode_of
# ---------------------------------------------------------------------------


class TestModeOf:
    """Tests for mode_of()."""

    @pytest.mark.parametrize("backend", ["openai", "gemini", "anthropic", "ollama"])
    def test_supported_backend_is_its_own_mode(self, backend: str) -> None:
        """A supported backend without api_version maps to itself."""
        assert mode_of(_config(backend=backend, model="m")) == backend

    def test_openai_with_api_version_is_azure(self) -> None:
        """api_version routes the openai backend into azure mode."""
        cfg = _config(backend="openai", model="m", api_version="2024-02-01")
        assert mode_of(cfg) == "azure"

    def test_unknown_backend_has_no_mode(self) -> None:
        """A typo'd backend has no contract mode."""
        assert mode_of(_config(backend="opnai", model="m")) is None

    def test_literal_azure_backend_has_no_mode(self) -> None:
        """'azure' is an internal mode, never a valid backend value."""
        assert mode_of(_config(backend="azure", model="m")) is None

    def test_unset_backend_has_no_mode(self) -> None:
        """An unset backend has no contract mode."""
        assert mode_of(_config(model="m")) is None


# ---------------------------------------------------------------------------
# openai (plain)
# ---------------------------------------------------------------------------


class TestOpenAIContract:
    """Contract rows for the plain openai backend."""

    def test_missing_api_key_is_an_error(self) -> None:
        """openai without a key or env var reports an api_key error."""
        findings = _by_key(validate(_config(backend="openai", model="gpt-4o")))
        assert findings["api_key"]["ok"] is False

    def test_missing_api_key_is_an_error_even_with_base_url(self) -> None:
        """A custom base_url does not excuse a missing key.

        langchain builds ``openai.AsyncOpenAI(api_key=None)`` regardless, so a
        keyless config can never construct a client — there is no relay
        exception.
        """
        cfg = _config(
            backend="openai", model="gpt-4o", base_url="https://relay.example.com/v1"
        )
        findings = _by_key(validate(cfg))
        assert findings["api_key"]["ok"] is False
        message = findings["api_key"]["value"]
        assert "api_key" in message
        assert "OPENAI_API_KEY" in message

    def test_keyless_base_url_config_fails_with_the_contract_message(self) -> None:
        """_create_chat_model raises the contract error, never the SDK's."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        cfg = _config(
            backend="openai", model="gpt-4o", base_url="https://relay.example.com/v1"
        )
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.create_openai_model"
        ) as mock_create:
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                _create_chat_model(cfg)
        mock_create.assert_not_called()

    def test_missing_model_is_an_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """model is required on every backend."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        findings = _by_key(validate(_config(backend="openai")))
        assert findings["model"]["ok"] is False

    def test_env_key_satisfies_the_rule(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OPENAI_API_KEY alone produces no findings."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        assert validate(_config(backend="openai", model="gpt-4o")) == []

    def test_base_url_is_optional(self) -> None:
        """A set base_url is neither required nor warned about."""
        cfg = _config(
            backend="openai",
            model="gpt-4o",
            api_key="k",
            base_url="https://relay.example.com/v1",
        )
        assert validate(cfg) == []


# ---------------------------------------------------------------------------
# openai + api_version (azure mode)
# ---------------------------------------------------------------------------


class TestAzureContract:
    """Contract rows for azure mode (openai + api_version)."""

    def test_missing_base_url_is_an_error(self) -> None:
        """Azure mode without base_url or AZURE_OPENAI_ENDPOINT errors."""
        cfg = _config(
            backend="openai", model="dep", api_key="k", api_version="2024-02-01"
        )
        findings = _by_key(validate(cfg))
        assert findings["base_url"]["ok"] is False
        assert "api_version" in findings["base_url"]["value"]
        assert "AZURE_OPENAI_ENDPOINT" in findings["base_url"]["value"]

    def test_azure_endpoint_env_satisfies_base_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AZURE_OPENAI_ENDPOINT resolves the base_url requirement."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://res.openai.azure.com/")
        cfg = _config(
            backend="openai", model="dep", api_key="k", api_version="2024-02-01"
        )
        assert validate(cfg) == []

    def test_openai_api_key_env_satisfies_azure_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An Azure config keyed off OPENAI_API_KEY produces no finding.

        Guards the mode-keyed ``_API_KEY_ENV`` lookup: keying by the raw
        backend would miss the ``azure`` row and hard-fail a working setup.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        cfg = _config(
            backend="openai",
            model="dep",
            base_url="https://res.openai.azure.com/",
            api_version="2024-02-01",
        )
        assert validate(cfg) == []

    def test_openai_api_key_env_lets_the_model_be_created(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_create_chat_model does not raise for that same config."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        cfg = _config(
            backend="openai",
            model="dep",
            base_url="https://res.openai.azure.com/",
            api_version="2024-02-01",
        )
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.create_openai_model"
        ) as mock_create:
            _create_chat_model(cfg)
        mock_create.assert_called_once()

    @pytest.mark.parametrize(
        "env_var", ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_AD_TOKEN"]
    )
    def test_azure_sdk_variables_satisfy_api_key(
        self, env_var: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The variables AzureOpenAI resolves itself satisfy the rule.

        ``create_openai_model`` passes ``api_key=None`` straight through, so
        ``openai.AzureOpenAI`` falls back to these two. The construction
        assertion keeps the table from drifting from that fallback chain.
        """
        from mcp_coder.llm.providers.langchain.openai_backend import (
            create_openai_model,
        )

        monkeypatch.setenv(env_var, "azure-secret")
        base_url = "https://res.openai.azure.com/"
        cfg = _config(
            backend="openai",
            model="dep",
            base_url=base_url,
            api_version="2024-02-01",
        )
        assert validate(cfg) == []
        create_openai_model("dep", None, base_url, "2024-02-01")

    def test_no_credential_at_all_names_every_variable(self) -> None:
        """The required-message enumerates the whole azure row."""
        cfg = _config(
            backend="openai",
            model="dep",
            base_url="https://res.openai.azure.com/",
            api_version="2024-02-01",
        )
        findings = _by_key(validate(cfg))
        assert findings["api_key"]["ok"] is False
        message = findings["api_key"]["value"]
        assert "OPENAI_API_KEY" in message
        assert "AZURE_OPENAI_API_KEY" in message
        assert "AZURE_OPENAI_AD_TOKEN" in message

    def test_create_chat_model_raises_the_contract_message(self) -> None:
        """The missing-base_url case surfaces as the contract ValueError."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        cfg = _config(
            backend="openai", model="dep", api_key="k", api_version="2024-02-01"
        )
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.create_openai_model"
        ) as mock_create:
            with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
                _create_chat_model(cfg)
        mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# gemini / anthropic
# ---------------------------------------------------------------------------


class TestIgnoredFields:
    """Fields a backend cannot act on produce warnings, not errors."""

    @pytest.mark.parametrize("backend", ["gemini", "anthropic"])
    @pytest.mark.parametrize(
        ("field", "value"),
        [("base_url", "https://example.com/v1"), ("api_version", "2024-02-01")],
    )
    def test_ignored_field_warns(self, backend: str, field: str, value: str) -> None:
        """A set-but-ignored field yields an ok=None warning naming it."""
        cfg = _config(backend=backend, model="m", api_key="k")
        cfg[field] = value
        findings = _by_key(validate(cfg))
        assert findings[field]["ok"] is None
        assert field in findings[field]["value"]
        assert backend in findings[field]["value"]

    def test_ollama_api_version_warns(self) -> None:
        """ollama ignores api_version as well."""
        cfg = _config(backend="ollama", model="llama3.1", api_version="2024-02-01")
        findings = _by_key(validate(cfg))
        assert findings["api_version"]["ok"] is None


class TestGeminiApiKeySources:
    """Every credential source gemini actually accepts."""

    @pytest.mark.parametrize("env_var", ["GEMINI_API_KEY", "GOOGLE_API_KEY"])
    def test_env_variable_satisfies_api_key(
        self, env_var: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both SDK variables satisfy the rule and build a model."""
        from mcp_coder.llm.providers.langchain.gemini_backend import (
            create_gemini_model,
        )

        monkeypatch.setenv(env_var, "g-secret")
        assert validate(_config(backend="gemini", model="gemini-2.0-flash")) == []
        create_gemini_model("gemini-2.0-flash", None)

    def test_vertex_flag_is_the_keyless_carve_out(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GOOGLE_GENAI_USE_VERTEXAI authenticates without a key."""
        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "1")
        assert validate(_config(backend="gemini", model="gemini-2.0-flash")) == []

    def test_vertex_flag_is_tested_for_presence_not_truthiness(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A falsy-looking value still satisfies the rule.

        Deliberately over-permissive: mirroring the SDK's truthiness parsing
        would risk a false required-error on a working setup, while this
        direction costs only a message the SDK itself still gives.
        """
        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "0")
        assert validate(_config(backend="gemini", model="gemini-2.0-flash")) == []

    def test_no_source_at_all_is_an_error(self) -> None:
        """With nothing set, gemini reports an api_key error naming both vars."""
        findings = _by_key(
            validate(_config(backend="gemini", model="gemini-2.0-flash"))
        )
        assert findings["api_key"]["ok"] is False
        message = findings["api_key"]["value"]
        assert "GEMINI_API_KEY" in message
        assert "GOOGLE_API_KEY" in message


# ---------------------------------------------------------------------------
# ollama
# ---------------------------------------------------------------------------


class TestOllamaContract:
    """ollama needs nothing but a model."""

    def test_model_only_is_clean(self) -> None:
        """No api_key and no base_url is a valid ollama config."""
        assert validate(_config(backend="ollama", model="llama3.1")) == []

    def test_base_url_and_api_key_are_optional(self) -> None:
        """Setting the optional fields produces no findings either."""
        cfg = _config(
            backend="ollama",
            model="llama3.1",
            api_key="k",
            base_url="http://localhost:11434",
        )
        assert validate(cfg) == []


# ---------------------------------------------------------------------------
# unsupported backends
# ---------------------------------------------------------------------------


class TestUnsupportedBackend:
    """Backends with no contract row."""

    @pytest.mark.parametrize("backend", ["opnai", "azure", None])
    def test_single_backend_error(self, backend: str | None) -> None:
        """One ok=False finding on 'backend', listing the supported names."""
        findings = validate(_config(backend=backend, model="m"))
        assert len(findings) == 1
        assert findings[0]["key"] == "backend"
        assert findings[0]["ok"] is False
        for name in ("openai", "gemini", "anthropic", "ollama"):
            assert name in findings[0]["value"]

    def test_create_chat_model_keeps_the_existing_wording(self) -> None:
        """_create_chat_model still raises 'Unsupported langchain backend'."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        with pytest.raises(ValueError, match="Unsupported langchain backend"):
            _create_chat_model(_config(backend="azure", model="m"))
