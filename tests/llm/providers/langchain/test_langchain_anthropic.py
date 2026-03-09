"""Tests for mcp_coder.llm.providers.langchain.anthropic."""

from unittest.mock import MagicMock, patch

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
