"""Tests for Ollama agent pre-flight capability check.

These tests verify the _ollama_preflight() helper in __init__.py which
runs check_ollama_tool_capability() at the top of _ask_agent() and
_ask_agent_stream() when backend == "ollama". A capability failure
must raise ValueError immediately, before any model creation or
agent thread spins up.
"""

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PROVIDER_MOD = "mcp_coder.llm.providers.langchain"
_MODELS_MOD = f"{_PROVIDER_MOD}._models"


def _make_config(backend: str = "ollama", model: str = "foo") -> dict[str, str | None]:
    """Build a minimal langchain config dict for testing."""
    return {
        "provider": "langchain",
        "backend": backend,
        "model": model,
        "api_key": None,
        "endpoint": None,
        "api_version": None,
    }


class TestAskAgentOllamaPreflight:
    """Pre-flight tool capability check in _ask_agent()."""

    def test_ask_agent_raises_when_ollama_capability_missing(self) -> None:
        """backend='ollama' + capability missing -> ValueError, run_agent not called."""
        mock_check = MagicMock(
            return_value={
                "ok": False,
                "value": "model 'foo' does not advertise the 'tools' capability",
            }
        )
        mock_run_agent = AsyncMock()
        with (
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent", mock_run_agent),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_PROVIDER_MOD}.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent

            with pytest.raises(ValueError, match="does not advertise"):
                _ask_agent(
                    question="x",
                    config=_make_config(),
                    session_id="s1",
                    mcp_config="/path/.mcp.json",
                )

        mock_run_agent.assert_not_called()

    def test_ask_agent_proceeds_when_ollama_capability_ok(self) -> None:
        """backend='ollama' + capability ok -> run_agent called normally."""
        mock_check = MagicMock(
            return_value={"ok": True, "value": "model 'foo' supports tools"}
        )
        mock_run_agent = AsyncMock(
            return_value=(
                "agent answer",
                [{"type": "human", "content": "x"}],
                {"agent_steps": 1, "total_tool_calls": 0, "tool_trace": []},
            )
        )
        with (
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent", mock_run_agent),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_PROVIDER_MOD}.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent

            result = _ask_agent(
                question="x",
                config=_make_config(),
                session_id="s1",
                mcp_config="/path/.mcp.json",
            )

        assert result["text"] == "agent answer"
        mock_run_agent.assert_called_once()
        mock_check.assert_called_once()

    def test_ask_agent_raises_import_error_when_ollama_client_missing(self) -> None:
        """backend='ollama' but ollama client absent -> ImportError with install hint."""
        mock_check = MagicMock()
        mock_run_agent = AsyncMock()
        with (
            patch.dict(sys.modules, {"ollama": None}),
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent", mock_run_agent),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_PROVIDER_MOD}.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent

            with pytest.raises(ImportError, match="langchain-ollama"):
                _ask_agent(
                    question="x",
                    config=_make_config(),
                    session_id="s1",
                    mcp_config="/path/.mcp.json",
                )

        mock_check.assert_not_called()
        mock_run_agent.assert_not_called()

    def test_ask_agent_does_not_call_capability_for_non_ollama_backends(self) -> None:
        """backend='openai' -> capability helper never invoked."""
        mock_check = MagicMock()
        mock_run_agent = AsyncMock(
            return_value=(
                "agent answer",
                [],
                {"agent_steps": 0, "total_tool_calls": 0, "tool_trace": []},
            )
        )
        with (
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent", mock_run_agent),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_PROVIDER_MOD}.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent

            _ask_agent(
                question="x",
                config=_make_config(backend="openai", model="gpt-4o"),
                session_id="s1",
                mcp_config="/path/.mcp.json",
            )

        mock_check.assert_not_called()


class TestAskAgentStreamOllamaPreflight:
    """Pre-flight tool capability check in _ask_agent_stream()."""

    def test_ask_agent_stream_raises_when_ollama_capability_missing(self) -> None:
        """capability missing -> ValueError on iter; no thread spins up."""
        mock_check = MagicMock(
            return_value={
                "ok": False,
                "value": "model 'foo' does not advertise the 'tools' capability",
            }
        )
        mock_thread_cls = MagicMock()
        with (
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent_stream"),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_PROVIDER_MOD}.threading.Thread", mock_thread_cls),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent_stream

            gen = _ask_agent_stream(
                question="x",
                config=_make_config(),
                session_id="s1",
                mcp_config="/path/.mcp.json",
            )
            with pytest.raises(ValueError, match="does not advertise"):
                list(gen)

        mock_thread_cls.assert_not_called()

    def test_ask_agent_stream_proceeds_when_ollama_capability_ok(self) -> None:
        """capability ok -> underlying stream runs."""
        mock_check = MagicMock(
            return_value={"ok": True, "value": "model 'foo' supports tools"}
        )

        async def _empty_stream(*_args: Any, **_kwargs: Any) -> Any:
            for _ in []:
                yield {"type": "done"}

        with (
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent_stream", _empty_stream),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent_stream

            gen = _ask_agent_stream(
                question="x",
                config=_make_config(),
                session_id="s1",
                mcp_config="/path/.mcp.json",
            )
            events = list(gen)

        assert events == []
        mock_check.assert_called_once()

    def test_ask_agent_stream_does_not_call_capability_for_non_ollama(self) -> None:
        """backend='anthropic' -> capability helper never invoked."""
        mock_check = MagicMock()

        async def _empty_stream(*_args: Any, **_kwargs: Any) -> Any:
            for _ in []:
                yield {"type": "done"}

        with (
            patch(f"{_MODELS_MOD}.check_ollama_tool_capability", mock_check),
            patch(f"{_PROVIDER_MOD}.agent._check_agent_dependencies"),
            patch(f"{_PROVIDER_MOD}.agent.run_agent_stream", _empty_stream),
            patch(f"{_PROVIDER_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_PROVIDER_MOD}.load_langchain_history", return_value=[]),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent_stream

            gen = _ask_agent_stream(
                question="x",
                config=_make_config(backend="anthropic", model="claude-3"),
                session_id="s1",
                mcp_config="/path/.mcp.json",
            )
            list(gen)

        mock_check.assert_not_called()
