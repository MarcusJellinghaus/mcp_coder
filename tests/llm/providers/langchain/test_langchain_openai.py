"""Tests for mcp_coder.llm.providers.langchain.openai."""

from unittest.mock import MagicMock, patch


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
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai

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
        self, monkeypatch: object
    ) -> None:
        """OPENAI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key="config-key",
                endpoint=None,
                api_version=None,
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == "env-key"

    def test_uses_config_api_key_when_env_not_set(self, monkeypatch: object) -> None:
        """Config api_key is used when OPENAI_API_KEY is not in the environment."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai

            ask_openai(
                "Hi",
                model="gpt-4o",
                api_key="config-key",
                endpoint=None,
                api_version=None,
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == "config-key"

    def test_passes_endpoint_as_base_url(self) -> None:
        """endpoint is passed to ChatOpenAI as base_url."""
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai

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
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai

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
                "mcp_coder.llm.providers.langchain.openai.AzureChatOpenAI"
            ) as MockAzure,
            patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat,
        ):
            MockAzure.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai

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
            assert kwargs.get("openai_api_version") == "2024-02-01"
