"""Tests for mcp_coder.llm.providers.langchain.openai_backend."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr


class TestCreateOpenaiModel:
    """Tests for create_openai_model() factory."""

    def test_env_var_takes_priority_over_config_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OPENAI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(model="gpt-4o", api_key="config-key")
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == SecretStr("env-key")

    def test_uses_config_api_key_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config api_key is used when OPENAI_API_KEY is not in the environment."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(model="gpt-4o", api_key="config-key")
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == SecretStr("config-key")

    def test_passes_base_url_to_client(self) -> None:
        """base_url is passed to ChatOpenAI as base_url."""
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(
                model="gpt-4o",
                api_key=None,
                base_url="https://custom.example.com/v1",
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("base_url") == "https://custom.example.com/v1"

    def test_timeout_is_forwarded_to_client(self) -> None:
        """timeout is passed to ChatOpenAI constructor."""
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(model="gpt-4o", api_key=None, timeout=60)
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 60

    def test_api_version_triggers_azure_chat_openai(self) -> None:
        """When api_version is set, AzureChatOpenAI is used instead of ChatOpenAI."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.AzureChatOpenAI"
            ) as MockAzure,
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
            ) as MockChat,
        ):
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(
                model="gpt-4o",
                api_key="k",
                base_url="https://my.openai.azure.com/",
                api_version="2024-02-01",
            )
            MockAzure.assert_called_once()
            MockChat.assert_not_called()
            _, kwargs = MockAzure.call_args
            assert kwargs.get("azure_deployment") == "gpt-4o"
            assert kwargs.get("api_version") == "2024-02-01"

    def test_returns_chat_openai_instance(self) -> None:
        """create_openai_model returns a ChatOpenAI instance by default."""
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            mock_instance = MagicMock()
            MockChat.return_value = mock_instance
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            result = create_openai_model(model="gpt-4o", api_key=None)
            assert result is mock_instance


class TestCreateOpenaiModelHttpClient:
    """Tests for HTTP client injection into OpenAI/Azure constructors."""

    def test_http_client_passed_to_chat_openai(self) -> None:
        """create_http_client result is passed as http_client to ChatOpenAI."""
        mock_sync_client = MagicMock(name="sync_http_client")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_http_client",
                return_value=mock_sync_client,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_async_http_client",
                return_value=MagicMock(),
            ),
        ):
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(model="gpt-4o", api_key="k")
            _, kwargs = MockChat.call_args
            assert kwargs["http_client"] is mock_sync_client

    def test_http_async_client_passed_to_chat_openai(self) -> None:
        """create_async_http_client result is passed as http_async_client to ChatOpenAI."""
        mock_async_client = MagicMock(name="async_http_client")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_http_client",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_async_http_client",
                return_value=mock_async_client,
            ),
        ):
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(model="gpt-4o", api_key="k")
            _, kwargs = MockChat.call_args
            assert kwargs["http_async_client"] is mock_async_client

    def test_http_client_passed_to_azure_chat_openai(self) -> None:
        """create_http_client result is passed as http_client to AzureChatOpenAI."""
        mock_sync_client = MagicMock(name="sync_http_client")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.AzureChatOpenAI"
            ) as MockAzure,
            patch("mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_http_client",
                return_value=mock_sync_client,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_async_http_client",
                return_value=MagicMock(),
            ),
        ):
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(
                model="gpt-4o",
                api_key="k",
                base_url="https://my.openai.azure.com/",
                api_version="2024-02-01",
            )
            _, kwargs = MockAzure.call_args
            assert kwargs["http_client"] is mock_sync_client

    def test_http_async_client_passed_to_azure_chat_openai(self) -> None:
        """create_async_http_client result is passed as http_async_client to AzureChatOpenAI."""
        mock_async_client = MagicMock(name="async_http_client")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.AzureChatOpenAI"
            ) as MockAzure,
            patch("mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_http_client",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.create_async_http_client",
                return_value=mock_async_client,
            ),
        ):
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            create_openai_model(
                model="gpt-4o",
                api_key="k",
                base_url="https://my.openai.azure.com/",
                api_version="2024-02-01",
            )
            _, kwargs = MockAzure.call_args
            assert kwargs["http_async_client"] is mock_async_client


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


class TestCreateOpenaiModelHttpClientOwnership:
    """Both clients are built before the constructor runs, so a raising
    constructor leaves nobody holding them. ``verify`` probes construction on
    every run, so that path leaks a pair whenever the contract is violated."""

    _BACKEND = "mcp_coder.llm.providers.langchain.openai_backend"

    def _build(
        self,
        client_class: str,
        side_effect: Exception | None,
        api_version: str | None = None,
    ) -> tuple[_StubHttpClient, _StubAsyncHttpClient]:
        sync_client = _StubHttpClient()
        async_client = _StubAsyncHttpClient()
        with (
            patch(f"{self._BACKEND}.{client_class}", side_effect=side_effect),
            patch(f"{self._BACKEND}.create_http_client", return_value=sync_client),
            patch(
                f"{self._BACKEND}.create_async_http_client", return_value=async_client
            ),
        ):
            from mcp_coder.llm.providers.langchain.openai_backend import (
                create_openai_model,
            )

            if side_effect is None:
                create_openai_model(
                    model="gpt-4o", api_key="k", api_version=api_version
                )
            else:
                with pytest.raises(type(side_effect)):
                    create_openai_model(
                        model="gpt-4o", api_key="k", api_version=api_version
                    )
        return sync_client, async_client

    def test_clients_closed_when_chat_openai_raises(self) -> None:
        sync_client, async_client = self._build("ChatOpenAI", ValueError("boom"))

        assert sync_client.close_calls == 1
        assert async_client.close_calls == 1

    def test_clients_closed_when_azure_chat_openai_raises(self) -> None:
        sync_client, async_client = self._build(
            "AzureChatOpenAI",
            ValueError("Must provide one of base_url or azure_endpoint"),
            "2024-02-01",
        )

        assert sync_client.close_calls == 1
        assert async_client.close_calls == 1

    def test_clients_stay_open_on_success(self) -> None:
        """The returned model owns them; closing here would break every call."""
        sync_client, async_client = self._build("ChatOpenAI", None)

        assert sync_client.close_calls == 0
        assert async_client.close_calls == 0
