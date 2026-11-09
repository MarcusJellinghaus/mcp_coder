"""Tests for ``bash_grants`` forwarding in prompt_llm / prompt_llm_stream."""

from unittest.mock import MagicMock, patch

from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream
from mcp_coder.llm.types import LLMResponseDict
from tests.llm.test_interface import PROJECT_DIR

GRANTS = ["Bash(git config probe.a 1)", "Bash(npm test)"]


def _response(provider: str) -> LLMResponseDict:
    return {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "ok",
        "session_id": "s",
        "provider": provider,
        "raw_response": {},
    }


class TestPromptLlmBashGrants:
    """prompt_llm forwards bash_grants on the Claude branch only."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_claude_receives_grants(self, mock_ask: MagicMock) -> None:
        """provider='claude' forwards bash_grants to ask_claude_code_cli."""
        mock_ask.return_value = _response("claude")

        prompt_llm(
            "Test", provider="claude", project_dir=PROJECT_DIR, bash_grants=GRANTS
        )

        assert mock_ask.call_args.kwargs["bash_grants"] == GRANTS

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_claude_default_is_none(self, mock_ask: MagicMock) -> None:
        """Without bash_grants, ask_claude_code_cli receives None."""
        mock_ask.return_value = _response("claude")

        prompt_llm("Test", provider="claude", project_dir=PROJECT_DIR)

        assert mock_ask.call_args.kwargs["bash_grants"] is None

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_ignores_grants(self, mock_ask: MagicMock) -> None:
        """provider='copilot' does not pass bash_grants."""
        mock_ask.return_value = _response("copilot")

        prompt_llm(
            "Test", provider="copilot", project_dir=PROJECT_DIR, bash_grants=GRANTS
        )

        assert "bash_grants" not in mock_ask.call_args.kwargs

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_langchain_ignores_grants(self, mock_ask: MagicMock) -> None:
        """provider='langchain' does not pass bash_grants."""
        mock_ask.return_value = _response("langchain")

        prompt_llm(
            "Test", provider="langchain", project_dir=PROJECT_DIR, bash_grants=GRANTS
        )

        assert "bash_grants" not in mock_ask.call_args.kwargs


class TestPromptLlmStreamBashGrants:
    """prompt_llm_stream forwards bash_grants on the Claude branch only."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_claude_stream_receives_grants(self, mock_stream: MagicMock) -> None:
        """provider='claude' forwards bash_grants to ask_claude_code_cli_stream."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(
            prompt_llm_stream(
                "Test", provider="claude", project_dir=PROJECT_DIR, bash_grants=GRANTS
            )
        )

        assert mock_stream.call_args.kwargs["bash_grants"] == GRANTS

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli_stream")
    def test_copilot_stream_ignores_grants(self, mock_stream: MagicMock) -> None:
        """provider='copilot' does not pass bash_grants."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(
            prompt_llm_stream(
                "Test", provider="copilot", project_dir=PROJECT_DIR, bash_grants=GRANTS
            )
        )

        assert "bash_grants" not in mock_stream.call_args.kwargs
