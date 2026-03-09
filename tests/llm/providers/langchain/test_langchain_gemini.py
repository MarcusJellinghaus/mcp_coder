"""Tests for mcp_coder.llm.providers.langchain.gemini."""

from unittest.mock import MagicMock, patch


class TestAskGemini:
    def _fake_ai_message(self, text: str = "response text") -> MagicMock:
        msg = MagicMock()
        msg.content = text
        msg.response_metadata = {"model_name": "gemini-1.5-pro"}
        msg.usage_metadata = {"input_tokens": 5, "output_tokens": 3}
        msg.id = "gemini-resp-abc"
        return msg

    def test_returns_text_and_raw_dict(self) -> None:
        """ask_gemini returns (text, dict) on success."""
        ai_msg = self._fake_ai_message("Hello from Gemini!")
        with patch(
            "mcp_coder.llm.providers.langchain.gemini.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini import ask_gemini

            text, raw = ask_gemini(
                "Hi",
                model="gemini-1.5-pro",
                api_key=None,
                messages=[],
            )
        assert text == "Hello from Gemini!"
        assert isinstance(raw, dict)
        assert raw["content"] == "Hello from Gemini!"

    def test_env_var_takes_priority_over_config_api_key(
        self, monkeypatch: object
    ) -> None:
        """GEMINI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini import ask_gemini

            ask_gemini(
                "Hi",
                model="gemini-1.5-pro",
                api_key="config-gemini-key",
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("google_api_key") == "env-gemini-key"

    def test_uses_config_api_key_when_env_not_set(self, monkeypatch: object) -> None:
        """Config api_key is used when GEMINI_API_KEY is not in the environment."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini import ask_gemini

            ask_gemini(
                "Hi",
                model="gemini-1.5-pro",
                api_key="config-gemini-key",
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("google_api_key") == "config-gemini-key"

    def test_timeout_is_forwarded_to_client(self) -> None:
        """timeout is passed to ChatGoogleGenerativeAI constructor."""
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini import ask_gemini

            ask_gemini(
                "Hi",
                model="gemini-1.5-pro",
                api_key=None,
                messages=[],
                timeout=45,
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 45
