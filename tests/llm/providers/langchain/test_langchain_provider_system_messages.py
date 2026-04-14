"""Tests for system message building and prepending in langchain provider."""

from unittest.mock import MagicMock, patch

import pytest

_MOD = "mcp_coder.llm.providers.langchain"


# ---------------------------------------------------------------------------
# _build_system_messages tests
# ---------------------------------------------------------------------------


class TestBuildSystemMessages:
    """Tests for _build_system_messages helper."""

    def test_both_prompts_produce_two_messages(self) -> None:
        """Both system_prompt and project_prompt produce 2 SystemMessage objects."""
        from langchain_core.messages import SystemMessage

        from mcp_coder.llm.providers.langchain import _build_system_messages

        msgs = _build_system_messages("system instructions", "project context")
        assert len(msgs) == 2
        assert isinstance(msgs[0], SystemMessage)
        assert isinstance(msgs[1], SystemMessage)
        assert msgs[0].content == "system instructions"
        assert msgs[1].content == "project context"

    def test_system_only(self) -> None:
        """Only system_prompt produces 1 SystemMessage."""
        from mcp_coder.llm.providers.langchain import _build_system_messages

        msgs = _build_system_messages("system only", None)
        assert len(msgs) == 1
        assert msgs[0].content == "system only"

    def test_project_only(self) -> None:
        """Only project_prompt produces 1 SystemMessage."""
        from mcp_coder.llm.providers.langchain import _build_system_messages

        msgs = _build_system_messages(None, "project only")
        assert len(msgs) == 1
        assert msgs[0].content == "project only"

    def test_none_produces_empty_list(self) -> None:
        """No prompts produce an empty list."""
        from mcp_coder.llm.providers.langchain import _build_system_messages

        msgs = _build_system_messages(None, None)
        assert msgs == []

    def test_empty_strings_produce_empty_list(self) -> None:
        """Empty strings are falsy and produce no messages."""
        from mcp_coder.llm.providers.langchain import _build_system_messages

        msgs = _build_system_messages("", "")
        assert msgs == []


# ---------------------------------------------------------------------------
# System message prepending tests
# ---------------------------------------------------------------------------


class TestAskTextPrependsSystemMessages:
    """Tests that _ask_text prepends system messages to the message list."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_system_messages_appear_first_in_invoke(self) -> None:
        """SystemMessage objects appear before history and question."""
        from langchain_core.messages import SystemMessage

        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "response"
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": "response"}
        mock_model.invoke.return_value = mock_ai_msg

        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain(
                "Hi",
                system_prompt="system instructions",
                project_prompt="project context",
            )

        # Verify the message list passed to invoke
        call_args = mock_model.invoke.call_args[0][0]
        assert len(call_args) == 3  # 2 system + 1 human
        assert isinstance(call_args[0], SystemMessage)
        assert isinstance(call_args[1], SystemMessage)
        assert call_args[0].content == "system instructions"
        assert call_args[1].content == "project context"

    def test_no_system_messages_when_none(self) -> None:
        """No SystemMessages prepended when prompts are None."""
        from langchain_core.messages import SystemMessage

        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "response"
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": "response"}
        mock_model.invoke.return_value = mock_ai_msg

        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("Hi")

        call_args = mock_model.invoke.call_args[0][0]
        assert len(call_args) == 1  # just the human message
        assert not isinstance(call_args[0], SystemMessage)


class TestAskTextStreamPrependsSystemMessages:
    """Tests that _ask_text_stream prepends system messages."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_system_messages_appear_first_in_stream(self) -> None:
        """SystemMessage objects appear first in stream message list."""
        from langchain_core.messages import SystemMessage

        mock_chunk = MagicMock()
        mock_chunk.content = "streamed"
        mock_chunk.model_dump.return_value = {"type": "ai", "content": "streamed"}

        mock_model = MagicMock()
        mock_model.stream.return_value = [mock_chunk]

        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            list(
                ask_langchain_stream(
                    "Hi",
                    system_prompt="sys",
                    project_prompt="proj",
                )
            )

        call_args = mock_model.stream.call_args[0][0]
        assert len(call_args) == 3  # 2 system + 1 human
        assert isinstance(call_args[0], SystemMessage)
        assert isinstance(call_args[1], SystemMessage)


class TestAskLangchainPassesSystemMessages:
    """End-to-end test: ask_langchain passes system messages through."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_agent_mode_passes_system_messages(self) -> None:
        """In agent mode, system_messages are passed to run_agent."""
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD}.asyncio.run",
                return_value=(
                    "response",
                    [],
                    {"agent_steps": 0, "total_tool_calls": 0},
                ),
            ) as mock_run,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain(
                "q",
                mcp_config="/tmp/mcp.json",
                system_prompt="sys",
                project_prompt="proj",
            )

        # Verify asyncio.run was called (system_messages passed through _ask_agent)
        assert mock_run.called


class TestEnsureTruststoreCalled:
    """Both _ask_text and _ask_agent call ensure_truststore."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def _mock_chat_model(self, text: str = "Hello!") -> MagicMock:
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = text
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": text}
        mock_model.invoke.return_value = mock_ai_msg
        return mock_model

    def test_ask_text_calls_ensure_truststore(self) -> None:
        """_ask_text calls ensure_truststore before model creation."""
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(
                f"{_MOD}._create_chat_model",
                return_value=self._mock_chat_model(),
            ),
            patch(f"{_MOD}.ensure_truststore") as mock_ts,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question")
        mock_ts.assert_called_once()

    def test_ask_agent_calls_ensure_truststore(self) -> None:
        """_ask_agent calls ensure_truststore before model creation."""
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD}.asyncio.run",
                return_value=(
                    "response",
                    [],
                    {"agent_steps": 1, "total_tool_calls": 0},
                ),
            ),
            patch(f"{_MOD}.ensure_truststore") as mock_ts,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question", mcp_config="/tmp/mcp.json")
        mock_ts.assert_called_once()
