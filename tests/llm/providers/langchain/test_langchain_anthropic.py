"""Tests for mcp_coder.llm.providers.langchain.anthropic."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr


class TestAskAnthropic:
    def _fake_ai_message(self, text: str = "response text") -> MagicMock:
        msg = MagicMock()
        msg.content = text
        msg.response_metadata = {"model": "claude-opus-4-6"}
        msg.usage_metadata = {"input_tokens": 5, "output_tokens": 3}
        msg.id = "msg_abc123"
        return msg

    def test_returns_text_and_raw_dict(self) -> None:
        """ask_anthropic returns (text, dict) on success."""
        ai_msg = self._fake_ai_message("Hello from Anthropic!")
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            text, raw = ask_anthropic(
                "Hi",
                model="claude-opus-4-6",
                api_key=None,
                messages=[],
            )
        assert text == "Hello from Anthropic!"
        assert isinstance(raw, dict)
        assert raw["content"] == "Hello from Anthropic!"

    def test_env_var_takes_priority_over_config_api_key(
        self, monkeypatch: object
    ) -> None:
        """ANTHROPIC_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-ant-key")  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            ask_anthropic(
                "Hi",
                model="claude-opus-4-6",
                api_key="config-ant-key",
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("anthropic_api_key") == SecretStr("env-ant-key")

    def test_uses_config_api_key_when_env_not_set(self, monkeypatch: object) -> None:
        """Config api_key is used when ANTHROPIC_API_KEY is not in the environment."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            ask_anthropic(
                "Hi",
                model="claude-opus-4-6",
                api_key="config-ant-key",
                messages=[],
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("anthropic_api_key") == SecretStr("config-ant-key")

    def test_timeout_is_forwarded_to_client(self) -> None:
        """timeout is passed to ChatAnthropic constructor as float."""
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            ask_anthropic(
                "Hi",
                model="claude-opus-4-6",
                api_key=None,
                messages=[],
                timeout=45,
            )
            _, kwargs = MockChat.call_args
            assert kwargs.get("default_request_timeout") == 45.0

    def test_no_api_key_passes_none(self, monkeypatch: object) -> None:
        """When no key is set anywhere, api_key=None is passed to ChatAnthropic."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # type: ignore[attr-defined]
        ai_msg = self._fake_ai_message()
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
        ) as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            ask_anthropic("Hi", model="claude-opus-4-6", api_key=None, messages=[])
            _, kwargs = MockChat.call_args
            assert kwargs.get("anthropic_api_key") is None

    def test_not_found_error_raises_value_error_with_model_list(self) -> None:
        """When API returns 404/not_found, ValueError includes available models."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.anthropic.list_anthropic_models",
                return_value=["claude-opus-4-6", "claude-sonnet-4-5-20250929"],
            ),
        ):
            MockChat.return_value.invoke.side_effect = Exception(
                "Error code: 404 - {'type': 'error', 'error': {'type': 'not_found_error'}}"
            )
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            with pytest.raises(ValueError) as exc_info:
                ask_anthropic("Hi", model="bad-model", api_key=None, messages=[])
        assert "bad-model" in str(exc_info.value)
        assert "claude-opus-4-6" in str(exc_info.value)

    def test_not_found_error_raised_even_when_model_listing_fails(self) -> None:
        """404 still raises ValueError even if listing available models fails."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
            ) as MockChat,
            patch(
                "mcp_coder.llm.providers.langchain.anthropic.list_anthropic_models",
                side_effect=Exception("network error"),
            ),
        ):
            MockChat.return_value.invoke.side_effect = Exception("404 not_found_error")
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            with pytest.raises(ValueError, match="not found"):
                ask_anthropic("Hi", model="bad-model", api_key=None, messages=[])

    def test_non_not_found_exception_is_reraised_unchanged(self) -> None:
        """Non-404 exceptions propagate as-is without wrapping."""
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic.ChatAnthropic"
        ) as MockChat:
            MockChat.return_value.invoke.side_effect = RuntimeError("network timeout")
            from mcp_coder.llm.providers.langchain.anthropic import ask_anthropic

            with pytest.raises(RuntimeError, match="network timeout"):
                ask_anthropic("Hi", model="claude-opus-4-6", api_key=None, messages=[])
