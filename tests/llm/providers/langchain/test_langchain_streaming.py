"""Tests for ask_langchain_stream / _ask_text_stream in langchain provider."""

import asyncio
import json
import threading
from collections.abc import AsyncIterator, Generator
from contextlib import AbstractContextManager, contextmanager
from unittest.mock import MagicMock, patch

import pytest

_MOD_LC = "mcp_coder.llm.providers.langchain"


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "endpoint": None,
        "api_version": None,
    }


def _mock_chunk(content: str) -> MagicMock:
    """Create a mock AIMessageChunk with given content."""
    chunk = MagicMock()
    chunk.content = content
    chunk.model_dump.return_value = {"type": "AIMessageChunk", "content": content}
    return chunk


class TestAskLangchainStreamTextYieldsDeltas:
    """ask_langchain_stream yields text_delta events from chat_model.stream()."""

    def test_text_yields_deltas(self) -> None:
        """Each chunk from chat_model.stream() becomes a text_delta event."""
        chunks = [_mock_chunk("Hello"), _mock_chunk(" world")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi"))

        text_deltas = [e for e in events if e["type"] == "text_delta"]
        assert len(text_deltas) == 2
        assert text_deltas[0]["text"] == "Hello"
        assert text_deltas[1]["text"] == " world"


class TestAskLangchainStreamTextYieldsRawLines:
    """ask_langchain_stream yields raw_line events for each chunk."""

    def test_text_yields_raw_lines(self) -> None:
        """Each chunk yields a raw_line event with JSON serialization."""
        chunks = [_mock_chunk("tok")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi"))

        raw_lines = [e for e in events if e["type"] == "raw_line"]
        assert len(raw_lines) == 1
        parsed = json.loads(str(raw_lines[0]["line"]))
        assert parsed["content"] == "tok"


class TestAskLangchainStreamTextYieldsDone:
    """ask_langchain_stream yields a done event with session_id."""

    def test_text_yields_done(self) -> None:
        """Stream ends with a done event containing the session_id."""
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([_mock_chunk("x")])

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi", session_id="sess-1"))

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["session_id"] == "sess-1"


class TestAskLangchainStreamTextStoresHistory:
    """ask_langchain_stream stores session history after streaming."""

    def test_text_stores_history(self) -> None:
        """store_langchain_history is called with correct messages."""
        chunks = [_mock_chunk("answer")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)
        store_mock = MagicMock()

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history", store_mock),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            list(ask_langchain_stream("q", session_id="sid"))

        store_mock.assert_called_once()
        args = store_mock.call_args[0]
        assert args[0] == "sid"  # session_id
        stored = args[1]
        types = [m["type"] for m in stored]
        assert types == ["human", "ai"]


# --- Helpers for agent stream tests ---


async def _mock_agent_stream_events(
    events: list[dict[str, object]],
) -> AsyncIterator[dict[str, object]]:
    """Create an async generator yielding predetermined StreamEvent dicts."""
    for evt in events:
        yield evt


def _patch_ask_agent_stream(
    stream_events: list[dict[str, object]],
) -> AbstractContextManager[None]:
    """Return a context manager that patches all deps for _ask_agent_stream."""

    async def _fake_run_agent_stream(
        **kwargs: object,
    ) -> AsyncIterator[dict[str, object]]:
        async for evt in _mock_agent_stream_events(stream_events):
            yield evt

    @contextmanager
    def _cm() -> Generator[None, None, None]:
        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.ensure_truststore"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
            patch(
                f"{_MOD_LC}.agent._check_agent_dependencies",
            ),
            patch(
                f"{_MOD_LC}.agent.run_agent_stream",
                side_effect=_fake_run_agent_stream,
            ),
        ):
            yield

    return _cm()


class TestAskLangchainStreamAgentReal:
    """Agent mode streams real events via thread+queue bridge."""

    def test_agent_streams_text_deltas(self) -> None:
        """Agent mode yields text_delta events from run_agent_stream."""
        stream_events: list[dict[str, object]] = [
            {"type": "text_delta", "text": "Hello"},
            {"type": "text_delta", "text": " world"},
        ]
        with _patch_ask_agent_stream(stream_events):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json"))

        text_deltas = [e for e in events if e["type"] == "text_delta"]
        assert len(text_deltas) == 2
        assert text_deltas[0]["text"] == "Hello"
        assert text_deltas[1]["text"] == " world"

    def test_agent_streams_tool_events(self) -> None:
        """Agent mode yields tool_use_start and tool_result events."""
        stream_events: list[dict[str, object]] = [
            {
                "type": "tool_use_start",
                "name": "search",
                "args": '{"q": "test"}',
                "tool_call_id": "tc-1",
            },
            {
                "type": "tool_result",
                "name": "search",
                "output": "found it",
                "tool_call_id": "tc-1",
            },
        ]
        with _patch_ask_agent_stream(stream_events):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json"))

        tool_starts = [e for e in events if e["type"] == "tool_use_start"]
        assert len(tool_starts) == 1
        assert tool_starts[0]["tool_call_id"] == "tc-1"

        tool_results = [e for e in events if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["tool_call_id"] == "tc-1"

    def test_agent_streams_raw_lines(self) -> None:
        """Agent mode yields raw_line events."""
        stream_events: list[dict[str, object]] = [
            {"type": "raw_line", "line": '{"event": "on_chat_model_stream"}'},
        ]
        with _patch_ask_agent_stream(stream_events):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json"))

        raw_lines = [e for e in events if e["type"] == "raw_line"]
        assert len(raw_lines) == 1

    def test_agent_streams_done_event(self) -> None:
        """Agent mode ends with done event."""
        stream_events: list[dict[str, object]] = [
            {"type": "text_delta", "text": "Hi"},
            {"type": "done", "session_id": "s1"},
        ]
        with _patch_ask_agent_stream(stream_events):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(
                ask_langchain_stream("Hi", session_id="s1", mcp_config="/tmp/mcp.json")
            )

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["session_id"] == "s1"

    def test_agent_error_propagation(self) -> None:
        """Errors from run_agent_stream propagate to caller."""

        async def _error_stream(
            **kwargs: object,
        ) -> AsyncIterator[dict[str, object]]:
            raise RuntimeError("agent boom")
            yield {}  # pragma: no cover  # pylint: disable=unreachable

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.ensure_truststore"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD_LC}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD_LC}.agent.run_agent_stream",
                side_effect=_error_stream,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(RuntimeError, match="agent boom"):
                list(ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json"))


class TestAskLangchainStreamAgentTimeouts:
    """Timeout and cancellation behavior for agent streaming."""

    def test_no_progress_timeout_raises(self) -> None:
        """If agent produces no events for NO_PROGRESS_TIMEOUT, TimeoutError raised."""

        async def _blocking_stream(
            **kwargs: object,
        ) -> AsyncIterator[dict[str, object]]:
            await asyncio.sleep(100)  # block forever
            yield {}  # pragma: no cover  # pylint: disable=unreachable

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.ensure_truststore"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD_LC}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD_LC}.agent.run_agent_stream",
                side_effect=_blocking_stream,
            ),
            patch(f"{_MOD_LC}._AGENT_NO_PROGRESS_TIMEOUT", 0.3),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(TimeoutError, match="no output"):
                list(ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json"))

    def test_overall_timeout_raises(self) -> None:
        """If total time exceeds OVERALL_TIMEOUT, TimeoutError raised."""

        async def _slow_stream(**kwargs: object) -> AsyncIterator[dict[str, object]]:
            for i in range(20):
                await asyncio.sleep(0.2)
                yield {"type": "text_delta", "text": f"chunk{i}"}

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.ensure_truststore"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD_LC}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD_LC}.agent.run_agent_stream",
                side_effect=_slow_stream,
            ),
            patch(f"{_MOD_LC}._AGENT_NO_PROGRESS_TIMEOUT", 5),
            patch(f"{_MOD_LC}._AGENT_OVERALL_TIMEOUT", 0.5),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(TimeoutError, match="overall timeout"):
                list(ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json"))

    def test_generator_exit_sets_cancel(self) -> None:
        """When consumer stops iterating, cancel_event is set."""
        cancel_was_set = threading.Event()

        async def _many_events_stream(
            **kwargs: object,
        ) -> AsyncIterator[dict[str, object]]:
            cancel_evt: threading.Event | None = kwargs.get("cancel_event")  # type: ignore[assignment]
            for i in range(100):
                if cancel_evt and cancel_evt.is_set():
                    cancel_was_set.set()
                    break
                yield {"type": "text_delta", "text": f"chunk{i}"}
                await asyncio.sleep(0.05)

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.ensure_truststore"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD_LC}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD_LC}.agent.run_agent_stream",
                side_effect=_many_events_stream,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            gen = ask_langchain_stream("Hi", mcp_config="/tmp/mcp.json")
            # Consume only first event, then close the generator
            first = next(gen)
            assert first["type"] == "text_delta"
            gen.close()  # type: ignore[attr-defined]

            # Give the background thread a moment to notice the cancel
            cancel_was_set.wait(timeout=2)
            assert cancel_was_set.is_set()


class TestAskLangchainStreamRoutesToText:
    """Without mcp_config, ask_langchain_stream routes to _ask_text_stream."""

    def test_routes_to_text_without_mcp_config(self) -> None:
        """No mcp_config means _ask_text_stream is used (chat_model.stream called)."""
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([_mock_chunk("hi")])

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            list(ask_langchain_stream("Hi"))

        mock_model.stream.assert_called_once()


class TestAskLangchainStreamErrorHandling:
    """ask_langchain_stream yields error event on provider errors."""

    def test_error_handling(self) -> None:
        """Provider error yields an error event and re-raises."""
        mock_model = MagicMock()
        mock_model.stream.side_effect = RuntimeError("boom")

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(RuntimeError, match="boom"):
                list(ask_langchain_stream("Hi"))
