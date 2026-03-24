"""Tests for mcp_coder.llm.providers.langchain.anthropic_backend."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr


class TestCreateAnthropicModel:
    """Tests for create_anthropic_model() factory."""

    def test_env_var_takes_priority_over_config_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ANTHROPIC_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-ant-key")
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            create_anthropic_model(model="claude-opus-4-6", api_key="config-ant-key")
            _, kwargs = MockChat.call_args
            assert kwargs.get("anthropic_api_key") == SecretStr("env-ant-key")

    def test_uses_config_api_key_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config api_key is used when ANTHROPIC_API_KEY is not in the environment."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            create_anthropic_model(model="claude-opus-4-6", api_key="config-ant-key")
            _, kwargs = MockChat.call_args
            assert kwargs.get("anthropic_api_key") == SecretStr("config-ant-key")

    def test_timeout_is_forwarded_to_client(self) -> None:
        """timeout is passed to ChatAnthropic constructor as float."""
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            create_anthropic_model(model="claude-opus-4-6", api_key=None, timeout=45)
            _, kwargs = MockChat.call_args
            assert kwargs.get("default_request_timeout") == 45.0

    def test_no_api_key_passes_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no key is set anywhere, api_key=None is passed to ChatAnthropic."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            create_anthropic_model(model="claude-opus-4-6", api_key=None)
            _, kwargs = MockChat.call_args
            assert kwargs.get("anthropic_api_key") is None

    def test_returns_chat_anthropic_instance(self) -> None:
        """create_anthropic_model returns a ChatAnthropic instance."""
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
        ) as MockChat:
            mock_instance = MagicMock()
            MockChat.return_value = mock_instance
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            result = create_anthropic_model(model="claude-opus-4-6", api_key=None)
            assert result is mock_instance


class TestCreateAnthropicModelHttpClient:
    """Tests for HTTP client injection into ChatAnthropic constructor."""

    def test_http_client_passed_to_chat_anthropic(self) -> None:
        """create_http_client result is passed as http_client to ChatAnthropic."""
        mock_sync_client = MagicMock(name="sync_http_client")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.anthropic_backend.create_http_client",
                return_value=mock_sync_client,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.anthropic_backend.create_async_http_client",
                return_value=MagicMock(),
            ),
        ):
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            create_anthropic_model(model="claude-opus-4-6", api_key="k")
            _, kwargs = MockChat.call_args
            assert kwargs["http_client"] is mock_sync_client

    def test_http_async_client_passed_to_chat_anthropic(self) -> None:
        """create_async_http_client result is passed as http_async_client to ChatAnthropic."""
        mock_async_client = MagicMock(name="async_http_client")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.anthropic_backend.ChatAnthropic"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.anthropic_backend.create_http_client",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.anthropic_backend.create_async_http_client",
                return_value=mock_async_client,
            ),
        ):
            from mcp_coder.llm.providers.langchain.anthropic_backend import (
                create_anthropic_model,
            )

            create_anthropic_model(model="claude-opus-4-6", api_key="k")
            _, kwargs = MockChat.call_args
            assert kwargs["http_async_client"] is mock_async_client
