"""Tests for mcp_coder.llm.providers.langchain.gemini_backend."""

import inspect
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr


class TestCreateGeminiModel:
    """Tests for create_gemini_model() factory."""

    def test_env_var_takes_priority_over_config_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GEMINI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.gemini_backend import (
                create_gemini_model,
            )

            create_gemini_model(model="gemini-1.5-pro", api_key="config-gemini-key")
            _, kwargs = MockChat.call_args
            assert kwargs.get("google_api_key") == SecretStr("env-gemini-key")

    def test_uses_config_api_key_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config api_key is used when GEMINI_API_KEY is not in the environment."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.gemini_backend import (
                create_gemini_model,
            )

            create_gemini_model(model="gemini-1.5-pro", api_key="config-gemini-key")
            _, kwargs = MockChat.call_args
            assert kwargs.get("google_api_key") == SecretStr("config-gemini-key")

    def test_env_var_api_key_wrapped_in_secret_str(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env var API key is wrapped in SecretStr like other backends."""
        monkeypatch.setenv("GEMINI_API_KEY", "secret-gemini-key")
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.gemini_backend import (
                create_gemini_model,
            )

            create_gemini_model(model="gemini-1.5-pro", api_key=None)
            _, kwargs = MockChat.call_args
            secret = kwargs.get("google_api_key")
            assert isinstance(secret, SecretStr)
            assert secret.get_secret_value() == "secret-gemini-key"

    def test_timeout_is_forwarded_to_client(self) -> None:
        """timeout is passed to ChatGoogleGenerativeAI constructor."""
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.gemini_backend import (
                create_gemini_model,
            )

            create_gemini_model(model="gemini-1.5-pro", api_key=None, timeout=45)
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 45

    def test_returns_chat_google_instance(self) -> None:
        """create_gemini_model returns a ChatGoogleGenerativeAI instance."""
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            mock_instance = MagicMock()
            MockChat.return_value = mock_instance
            from mcp_coder.llm.providers.langchain.gemini_backend import (
                create_gemini_model,
            )

            result = create_gemini_model(model="gemini-1.5-pro", api_key=None)
            assert result is mock_instance


class TestGeminiSdkLimitation:
    """Tests documenting Gemini SDK HTTP client limitation."""

    def test_gemini_limitation_documented(self) -> None:
        """Verify create_gemini_model has a comment about SDK limitation (#562)."""
        import mcp_coder.llm.providers.langchain.gemini_backend as mod

        source = inspect.getsource(mod)
        assert "does not support custom httpx clients" in source
        assert "#562" in source
