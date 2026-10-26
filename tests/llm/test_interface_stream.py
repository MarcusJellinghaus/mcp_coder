from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import prompt_llm_stream
from tests.llm.test_interface import PROJECT_DIR


class TestPromptLlmStream:
    """Tests for prompt_llm_stream() function."""

    def test_prompt_llm_stream_validates_empty_question(self) -> None:
        """prompt_llm_stream raises ValueError for empty question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            list(prompt_llm_stream("", project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_whitespace_question(self) -> None:
        """prompt_llm_stream raises ValueError for whitespace-only question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            list(prompt_llm_stream("   ", project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_timeout_zero(self) -> None:
        """prompt_llm_stream raises ValueError for timeout <= 0."""
        with pytest.raises(ValueError, match="positive number"):
            list(prompt_llm_stream("Test", timeout=0, project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_timeout_negative(self) -> None:
        """prompt_llm_stream raises ValueError for negative timeout."""
        with pytest.raises(ValueError, match="positive number"):
            list(prompt_llm_stream("Test", timeout=-5, project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_provider(self) -> None:
        """prompt_llm_stream raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            list(prompt_llm_stream("Test", provider="gpt", project_dir=PROJECT_DIR))

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_routes_to_claude(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream routes to ask_claude_code_cli_stream for claude provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream("Hello", provider="claude", project_dir=PROJECT_DIR)
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert len(events) == 2
        assert events[0]["type"] == "text_delta"

    @patch("mcp_coder.llm.providers.langchain.ask_langchain_stream")
    def test_prompt_llm_stream_routes_to_langchain(
        self, mock_stream: MagicMock
    ) -> None:
        """prompt_llm_stream routes to ask_langchain_stream for langchain provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream("Hello", provider="langchain", project_dir=PROJECT_DIR)
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            env_vars=None,
            tools=None,
            system_prompt=None,
            project_prompt=None,
            approval_bridge=None,
        )
        assert len(events) == 2

    def test_prompt_llm_stream_explicit_provider_beats_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicitly passed provider wins over MCP_CODER_LLM_PROVIDER."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.ask_langchain_stream",
                return_value=iter([{"type": "done", "usage": {}}]),
            ) as mock_langchain,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli_streaming."
                "ask_claude_code_cli_stream",
                return_value=iter([{"type": "done", "usage": {}}]),
            ) as mock_claude,
        ):
            events = list(
                prompt_llm_stream("Hello", provider="claude", project_dir=PROJECT_DIR)
            )

        mock_langchain.assert_not_called()
        mock_claude.assert_called_once()
        assert len(events) == 1

    def test_prompt_llm_stream_env_var_used_when_provider_omitted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_PROVIDER applies when no provider argument is given."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain_stream",
            return_value=iter([{"type": "done", "usage": {}}]),
        ) as mock_langchain:
            events = list(prompt_llm_stream("Hello", project_dir=PROJECT_DIR))

        mock_langchain.assert_called_once()
        assert len(events) == 1

    def test_prompt_llm_stream_defaults_to_claude_without_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no provider argument and no env var, claude is used."""
        monkeypatch.delenv("MCP_CODER_LLM_PROVIDER", raising=False)
        with patch(
            "mcp_coder.llm.providers.claude.claude_code_cli_streaming."
            "ask_claude_code_cli_stream",
            return_value=iter([{"type": "done", "usage": {}}]),
        ) as mock_claude:
            events = list(prompt_llm_stream("Hello", project_dir=PROJECT_DIR))

        mock_claude.assert_called_once()
        assert len(events) == 1

    def test_prompt_llm_stream_unsupported_provider_still_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit unsupported provider raises even with a valid env var set."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with pytest.raises(ValueError, match="Unsupported provider: unsupported_xyz"):
            list(
                prompt_llm_stream(
                    "Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR
                )
            )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_passes_all_params(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream passes all parameters to the claude provider."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(
            prompt_llm_stream(
                "Q",
                provider="claude",
                session_id="sid",
                timeout=60,
                env_vars={"K": "V"},
                project_dir="/work",
                mcp_config="/mcp.json",
                branch_name="main",
            )
        )

        mock_stream.assert_called_once_with(
            "Q",
            session_id="sid",
            timeout=60,
            env_vars={"K": "V"},
            cwd=str(Path("/work")),
            mcp_config="/mcp.json",
            settings_file=None,
            branch_name="main",
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )


class TestPromptLlmStreamToolsParam:
    """Tests for tools parameter threading in prompt_llm_stream()."""

    @patch("mcp_coder.llm.providers.langchain.ask_langchain_stream")
    def test_prompt_llm_stream_passes_tools_to_langchain(
        self, mock_stream: MagicMock
    ) -> None:
        """prompt_llm_stream forwards tools= to ask_langchain_stream for langchain provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )
        fake_tools: list[Any] = [MagicMock(), MagicMock()]

        events = list(
            prompt_llm_stream(
                "Hello",
                provider="langchain",
                tools=fake_tools,
                project_dir=PROJECT_DIR,
            )
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            env_vars=None,
            tools=fake_tools,
            system_prompt=None,
            project_prompt=None,
            approval_bridge=None,
        )
        assert len(events) == 2

    @patch("mcp_coder.llm.providers.langchain.ask_langchain_stream")
    def test_prompt_llm_stream_passes_none_tools_by_default(
        self, mock_stream: MagicMock
    ) -> None:
        """prompt_llm_stream passes tools=None when no tools argument given."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(prompt_llm_stream("Hello", provider="langchain", project_dir=PROJECT_DIR))

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            env_vars=None,
            tools=None,
            system_prompt=None,
            project_prompt=None,
            approval_bridge=None,
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_claude_ignores_tools(
        self, mock_stream: MagicMock
    ) -> None:
        """Claude path works fine with tools param present (tools not forwarded to claude)."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream(
                "Hello",
                provider="claude",
                tools=[MagicMock()],
                project_dir=PROJECT_DIR,
            )
        )

        # Claude provider call should NOT include tools kwarg
        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert len(events) == 2
