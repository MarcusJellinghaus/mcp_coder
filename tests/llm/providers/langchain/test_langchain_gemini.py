"""Tests for mcp_coder.llm.providers.langchain.gemini_backend."""

from unittest.mock import MagicMock, patch

import pytest


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
            assert kwargs.get("google_api_key") == "env-gemini-key"

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
            assert kwargs.get("google_api_key") == "config-gemini-key"

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
