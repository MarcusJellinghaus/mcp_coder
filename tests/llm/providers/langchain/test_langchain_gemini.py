"""Tests for mcp_coder.llm.providers.langchain.gemini_backend."""

from unittest.mock import MagicMock, patch

import pytest


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
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

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
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GEMINI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

            ask_gemini(
                "Hi",
                model="gemini-1.5-pro",
                api_key="config-gemini-key",
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("google_api_key") == "env-gemini-key"

    def test_uses_config_api_key_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config api_key is used when GEMINI_API_KEY is not in the environment."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

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
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

            ask_gemini(
                "Hi",
                model="gemini-1.5-pro",
                api_key=None,
                messages=[],
                timeout=45,
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 45

    def test_not_found_error_raises_value_error_with_model_list(self) -> None:
        """When API returns NOT_FOUND, ValueError includes available models."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.gemini_backend.list_gemini_models",
                return_value=["gemini-2.0-flash", "gemini-2.5-pro"],
            ),
        ):
            MockChat.return_value.invoke.side_effect = Exception(
                "Error calling model 'bad-model' (NOT_FOUND): 404 NOT_FOUND"
            )
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

            with pytest.raises(ValueError) as exc_info:
                ask_gemini("Hi", model="bad-model", api_key=None, messages=[])
        assert "bad-model" in str(exc_info.value)
        assert "gemini-2.0-flash" in str(exc_info.value)

    def test_not_found_error_raised_even_when_model_listing_fails(self) -> None:
        """NOT_FOUND still raises ValueError even if listing available models fails."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.gemini_backend.list_gemini_models",
                side_effect=Exception("network error"),
            ),
        ):
            MockChat.return_value.invoke.side_effect = Exception("NOT_FOUND 404")
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

            with pytest.raises(ValueError, match="not found"):
                ask_gemini("Hi", model="bad-model", api_key=None, messages=[])

    def test_non_not_found_exception_is_reraised_unchanged(self) -> None:
        """Non-NOT_FOUND exceptions propagate as-is without wrapping."""
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.ChatGoogleGenerativeAI"
        ) as MockChat:
            MockChat.return_value.invoke.side_effect = RuntimeError("network timeout")
            from mcp_coder.llm.providers.langchain.gemini_backend import ask_gemini

            with pytest.raises(RuntimeError, match="network timeout"):
                ask_gemini("Hi", model="gemini-2.0-flash", api_key=None, messages=[])
