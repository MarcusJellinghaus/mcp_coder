"""Tests for run_agent_stream() in langchain agent provider."""

import threading
from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

_AGENT_MOD_PATH = "mcp_coder.llm.providers.langchain.agent"
_STORAGE_MOD_PATH = "mcp_coder.llm.storage.session_storage"


async def _async_events(
    items: list[dict[str, object]],
) -> AsyncIterator[dict[str, object]]:
    """Create an async iterator from a list of event dicts."""
    for item in items:
        yield item


@contextmanager
def _patch_run_agent_stream(
    events: list[dict[str, object]],
    store_mock: MagicMock | None = None,
) -> Generator[MagicMock, None, None]:
    """Context manager with all patches needed for run_agent_stream tests."""
    mock_agent = MagicMock()
    mock_agent.astream_events.return_value = _async_events(events)

    mock_client_cls = MagicMock()
    mock_client_cls.return_value.connections = {}

    _store = store_mock or MagicMock()

    with (
        patch(f"{_AGENT_MOD_PATH}._load_mcp_server_config", return_value={}),
        patch(
            "langchain_mcp_adapters.client.MultiServerMCPClient",
            mock_client_cls,
        ),
        patch(
            "langgraph.prebuilt.create_react_agent",
            return_value=mock_agent,
        ),
        patch(f"{_STORAGE_MOD_PATH}.store_langchain_history", _store),
    ):
        yield _store


class TestRunAgentStream:
    """Tests for run_agent_stream() async generator event mapping."""

    async def test_text_delta_from_chat_model_stream(self) -> None:
        """on_chat_model_stream events become text_delta StreamEvents."""
        chunk = MagicMock()
        chunk.content = "Hello"
        events: list[dict[str, object]] = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk},
                "run_id": "r1",
                "name": "model",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        text_deltas = [e for e in result if e["type"] == "text_delta"]
        assert len(text_deltas) == 1
        assert text_deltas[0]["text"] == "Hello"

    async def test_text_delta_list_content_format(self) -> None:
        """AIMessageChunk with list-of-blocks content is handled."""
        chunk = MagicMock()
        chunk.content = [{"type": "text", "text": "Hello"}]
        events: list[dict[str, object]] = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk},
                "run_id": "r1",
                "name": "model",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        text_deltas = [e for e in result if e["type"] == "text_delta"]
        assert len(text_deltas) == 1
        assert text_deltas[0]["text"] == "Hello"

    async def test_tool_use_start_from_on_tool_start(self) -> None:
        """on_tool_start events become tool_use_start StreamEvents."""
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_start",
                "data": {"input": {"query": "test"}},
                "run_id": "run-1",
                "name": "search_tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_starts = [e for e in result if e["type"] == "tool_use_start"]
        assert len(tool_starts) == 1
        assert tool_starts[0]["name"] == "search_tool"
        assert tool_starts[0]["args"] == {"query": "test"}
        assert tool_starts[0]["tool_call_id"] == "run-1"

    async def test_tool_result_from_on_tool_end(self) -> None:
        """on_tool_end events become tool_result StreamEvents."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-123"
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "search_tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["name"] == "search_tool"
        assert tool_results[0]["tool_call_id"] == "tc-123"

    async def test_raw_line_emitted_for_every_event(self) -> None:
        """Every astream_events dict is also emitted as raw_line."""
        chunk = MagicMock()
        chunk.content = "Hi"
        events: list[dict[str, object]] = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk},
                "run_id": "r1",
                "name": "model",
            },
            {
                "event": "on_tool_start",
                "data": {"input": {}},
                "run_id": "r2",
                "name": "tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        raw_lines = [e for e in result if e["type"] == "raw_line"]
        assert len(raw_lines) == 2

    async def test_done_event_emitted_last(self) -> None:
        """Stream ends with done event containing session_id."""
        events: list[dict[str, object]] = []
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="sess-42",
                )
            ]
        assert result[-1]["type"] == "done"
        assert result[-1]["session_id"] == "sess-42"

    async def test_history_stored_before_done(self) -> None:
        """store_langchain_history called before done event is yielded."""
        chunk = MagicMock()
        chunk.content = "response"
        events: list[dict[str, object]] = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk},
                "run_id": "r1",
                "name": "model",
            },
        ]
        store_mock = MagicMock()
        with _patch_run_agent_stream(events, store_mock=store_mock):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        store_mock.assert_called_once()
        call_args = store_mock.call_args[0]
        assert call_args[0] == "s1"  # session_id
        done_events = [e for e in result if e["type"] == "done"]
        assert len(done_events) == 1

    async def test_error_propagation(self) -> None:
        """Errors from astream_events propagate as error event + exception."""

        async def _error_events() -> AsyncIterator[dict[str, object]]:
            if False:  # pylint: disable=using-constant-test
                yield  # make this an async generator
            raise RuntimeError("agent error")

        mock_agent = MagicMock()
        mock_agent.astream_events.return_value = _error_events()
        mock_client_cls = MagicMock()
        mock_client_cls.return_value.connections = {}

        with (
            patch(
                f"{_AGENT_MOD_PATH}._load_mcp_server_config",
                return_value={},
            ),
            patch(
                "langchain_mcp_adapters.client.MultiServerMCPClient",
                mock_client_cls,
            ),
            patch(
                "langgraph.prebuilt.create_react_agent",
                return_value=mock_agent,
            ),
            patch(f"{_STORAGE_MOD_PATH}.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            collected: list[dict[str, object]] = []
            with pytest.raises(RuntimeError, match="agent error"):
                async for evt in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                ):
                    collected.append(evt)
        error_events = [e for e in collected if e["type"] == "error"]
        assert len(error_events) == 1
        assert "agent error" in str(error_events[0]["message"])

    async def test_cancel_event_stops_stream(self) -> None:
        """Setting cancel_event stops the async generator."""
        cancel = threading.Event()

        async def _cancelling_events() -> AsyncIterator[dict[str, object]]:
            chunk1 = MagicMock()
            chunk1.content = "first"
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk1},
                "run_id": "r1",
                "name": "model",
            }
            cancel.set()
            chunk2 = MagicMock()
            chunk2.content = "second"
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk2},
                "run_id": "r2",
                "name": "model",
            }
            chunk3 = MagicMock()
            chunk3.content = "third"
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk3},
                "run_id": "r3",
                "name": "model",
            }

        mock_agent = MagicMock()
        mock_agent.astream_events.return_value = _cancelling_events()
        mock_client_cls = MagicMock()
        mock_client_cls.return_value.connections = {}

        with (
            patch(
                f"{_AGENT_MOD_PATH}._load_mcp_server_config",
                return_value={},
            ),
            patch(
                "langchain_mcp_adapters.client.MultiServerMCPClient",
                mock_client_cls,
            ),
            patch(
                "langgraph.prebuilt.create_react_agent",
                return_value=mock_agent,
            ),
            patch(f"{_STORAGE_MOD_PATH}.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                    cancel_event=cancel,
                )
            ]
        text_deltas = [e for e in result if e["type"] == "text_delta"]
        assert len(text_deltas) == 1
        assert text_deltas[0]["text"] == "first"
        done_events = [e for e in result if e["type"] == "done"]
        assert len(done_events) == 1
