"""Tests for mcp_coder.llm.providers.langchain.openai_backend."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr


class TestAskOpenai:
    def _fake_ai_message(self, text: str = "response text") -> MagicMock:
        msg = MagicMock()
        msg.content = text
        msg.response_metadata = {"model_name": "gpt-4o"}
        msg.usage_metadata = {"input_tokens": 5, "output_tokens": 3}
        msg.id = "chatcmpl-abc"
        return msg

    def test_returns_text_and_raw_dict(self) -> None:
        """ask_openai returns (text, dict) on success."""
        ai_msg = self._fake_ai_message("Hello!")
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            text, raw = ask_openai(
                "Hi",
                model="gpt-4o",
                api_key=None,
                endpoint=None,
                api_version=None,
                messages=[],
            )
        assert text == "Hello!"
        assert isinstance(raw, dict)
        assert raw["content"] == "Hello!"

    def test_env_var_takes_priority_over_config_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OPENAI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key="config-key",
                endpoint=None,
                api_version=None,
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == SecretStr("env-key")

    def test_uses_config_api_key_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config api_key is used when OPENAI_API_KEY is not in the environment."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key="config-key",
                endpoint=None,
                api_version=None,
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == SecretStr("config-key")

    def test_passes_endpoint_as_base_url(self) -> None:
        """endpoint is passed to ChatOpenAI as base_url."""
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key=None,
                endpoint="https://custom.example.com/v1",
                api_version=None,
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("base_url") == "https://custom.example.com/v1"

    def test_timeout_is_forwarded_to_client(self) -> None:
        """timeout is passed to ChatOpenAI constructor."""
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key=None,
                endpoint=None,
                api_version=None,
                messages=[],
                timeout=60,
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 60

    def test_api_version_triggers_azure_chat_openai(self) -> None:
        """When api_version is set, AzureChatOpenAI is used instead of ChatOpenAI."""
        ai_msg = self._fake_ai_message()
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.AzureChatOpenAI"
            ) as MockAzure,
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
            ) as MockChat,
        ):
            MockAzure.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key="k",
                endpoint="https://my.openai.azure.com/",
                api_version="2024-02-01",
                messages=[],
            )
            MockAzure.assert_called_once()
            MockChat.assert_not_called()
            _, kwargs = MockAzure.call_args
            assert kwargs.get("azure_deployment") == "gpt-4o"
            assert kwargs.get("api_version") == "2024-02-01"

    def test_not_found_error_raises_value_error_with_model_list(self) -> None:
        """When API returns 404, ValueError includes available models."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.list_openai_models",
                return_value=["gpt-3.5-turbo", "gpt-4o"],
            ),
        ):
            MockChat.return_value.invoke.side_effect = Exception(
                "Error code: 404 - The model 'bad-model' does not exist"
            )
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            with pytest.raises(ValueError) as exc_info:
                ask_openai(
                    "Hi",
                    model="bad-model",
                    api_key=None,
                    endpoint=None,
                    api_version=None,
                    messages=[],
                )
        assert "bad-model" in str(exc_info.value)
        assert "gpt-4o" in str(exc_info.value)

    def test_not_found_error_raised_even_when_model_listing_fails(self) -> None:
        """404 still raises ValueError even if listing available models fails."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.list_openai_models",
                side_effect=Exception("network error"),
            ),
        ):
            MockChat.return_value.invoke.side_effect = Exception(
                "Error code: 404 - not_found"
            )
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            with pytest.raises(ValueError, match="not found"):
                ask_openai(
                    "Hi",
                    model="bad-model",
                    api_key=None,
                    endpoint=None,
                    api_version=None,
                    messages=[],
                )

    def test_non_not_found_exception_is_reraised_unchanged(self) -> None:
        """Non-404 exceptions propagate as-is without wrapping."""
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.ChatOpenAI"
        ) as MockChat:
            MockChat.return_value.invoke.side_effect = RuntimeError("network timeout")
            from mcp_coder.llm.providers.langchain.openai_backend import ask_openai

            with pytest.raises(RuntimeError, match="network timeout"):
                ask_openai(
                    "Hi",
                    model="gpt-4o",
                    api_key=None,
                    endpoint=None,
                    api_version=None,
                    messages=[],
                )
