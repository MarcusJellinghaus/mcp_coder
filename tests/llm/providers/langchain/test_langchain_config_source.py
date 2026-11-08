"""Tests for mcp_coder.llm.providers.langchain._config_source."""

import logging
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain._config_source import _load_langchain_config

_GET_CONFIG_VALUES = (
    "mcp_coder.llm.providers.langchain._config_source.get_config_values"
)


class TestLoadLangchainConfig:
    """Tests for _load_langchain_config function."""

    def test_returns_expected_keys(self) -> None:
        """_load_langchain_config returns a dict with all expected keys."""
        with patch(
            _GET_CONFIG_VALUES,
            return_value={
                ("llm", "default_provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "base_url"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            cfg = _load_langchain_config()
        assert set(cfg.keys()) == {
            "default_provider",
            "backend",
            "model",
            "api_key",
            "base_url",
            "api_version",
        }

    def test_env_var_overrides_config_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_LANGCHAIN_* env vars override config.toml values.

        Env var overrides are now handled by get_config_values() via the schema,
        so the mock returns values as if env vars were already resolved.
        """
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", raising=False)
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_MODEL", raising=False)
        with patch(
            _GET_CONFIG_VALUES,
            return_value={
                ("llm", "default_provider"): "langchain",
                ("llm.langchain", "backend"): "gemini",
                ("llm.langchain", "model"): "gemini-2.0-flash",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "base_url"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            cfg = _load_langchain_config()
        assert cfg["backend"] == "gemini"
        assert cfg["model"] == "gemini-2.0-flash"

    def test_env_var_does_not_override_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty env vars do not override config.toml values."""
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", raising=False)
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_MODEL", raising=False)
        with patch(
            _GET_CONFIG_VALUES,
            return_value={
                ("llm", "default_provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "base_url"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            cfg = _load_langchain_config()
        assert cfg["backend"] == "openai"
        assert cfg["model"] == "gpt-4o"

    def test_base_url_env_var_is_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MCP_CODER_LLM_LANGCHAIN_BASE_URL lands under the 'base_url' key."""
        monkeypatch.setenv(
            "MCP_CODER_LLM_LANGCHAIN_BASE_URL", "https://relay.example.com/v1"
        )
        with patch(
            "mcp_coder.utils.user_config.load_config",
            return_value={},
        ):
            cfg = _load_langchain_config()
        assert cfg["base_url"] == "https://relay.example.com/v1"

    def test_retired_endpoint_env_var_is_ignored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_LANGCHAIN_ENDPOINT is no longer read (no alias)."""
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_BASE_URL", raising=False)
        monkeypatch.setenv(
            "MCP_CODER_LLM_LANGCHAIN_ENDPOINT", "https://retired.example.com/v1"
        )
        with patch(
            "mcp_coder.utils.user_config.load_config",
            return_value={},
        ):
            cfg = _load_langchain_config()
        assert cfg["base_url"] is None
        assert "endpoint" not in cfg

    def test_schema_type_mismatch_degrades_to_none(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A ValueError from get_config_values yields all-None values, not a raise.

        The loader runs on every ``verify``, including for claude users, so a
        mistyped ``[llm.langchain]`` value must not turn a clean config error
        into a traceback.
        """
        with patch(
            _GET_CONFIG_VALUES,
            side_effect=ValueError(
                "Config error in [llm.langchain] model: expected str, got int"
            ),
        ):
            with caplog.at_level(
                logging.WARNING, logger="mcp_coder.llm.providers.langchain"
            ):
                cfg = _load_langchain_config()

        assert cfg == {
            "default_provider": None,
            "backend": None,
            "model": None,
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }
        assert "llm.langchain" in caplog.text
        assert "mcp-coder verify" in caplog.text

    def test_non_str_values_narrow_to_none(self) -> None:
        """Values that survive the schema but are not str still narrow to None."""
        with patch(
            _GET_CONFIG_VALUES,
            return_value={
                ("llm", "default_provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): 123,
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "base_url"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            cfg = _load_langchain_config()

        assert cfg["backend"] == "openai"
        assert cfg["model"] is None
