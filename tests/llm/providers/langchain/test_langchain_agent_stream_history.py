"""Storage / ``done``-payload tests for ``run_agent_stream``.

These live apart from ``test_langchain_agent_streaming.py`` (which covers event
mapping) because that file is already close to the CI-enforced 750-line
file-size gate.

They all cover the same contract: the persisted history is the *graph's* final
message list, serialized by the shared helper (and therefore system-free), and
it is written exactly once — never on a cancelled or errored turn. The last test
covers the other end of the same contract: ``messages`` and ``stats`` never
cross the provider boundary.
"""

import threading
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Optional, cast
from unittest.mock import MagicMock, patch

import pytest

from tests.llm.providers.langchain.conftest import graph_events
from tests.llm.providers.langchain.test_langchain_agent_streaming import (
    _patch_run_agent_stream,
    _RaisingAsyncIter,
)

_MOD_LC = "mcp_coder.llm.providers.langchain"
_AGENT_MOD_PATH = "mcp_coder.llm.providers.langchain.agent"
_STORAGE_MOD_PATH = "mcp_coder.llm.storage.session_storage"


def _text_delta_event(text: str, run_id: str = "r1") -> dict[str, object]:
    """Build an ``on_chat_model_stream`` event carrying *text*."""
    chunk = MagicMock()
    chunk.content = text
    return {
        "event": "on_chat_model_stream",
        "data": {"chunk": chunk},
        "run_id": run_id,
        "name": "model",
    }


async def _collect(
    events: list[dict[str, object]],
    store_mock: MagicMock,
    **kwargs: Any,
) -> list[dict[str, object]]:
    """Run ``run_agent_stream`` over *events* and return the yielded events."""
    with _patch_run_agent_stream(events, store_mock=store_mock):
        from mcp_coder.llm.providers.langchain.agent import run_agent_stream

        return [
            e
            async for e in run_agent_stream(
                question="Hi",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path="/tmp/mcp.json",
                session_id="s1",
                **kwargs,
            )
        ]


class TestRunAgentStreamHistory:
    """The graph's final message list is what gets persisted."""

    async def test_stored_history_has_no_system_messages(self) -> None:
        """The prepended SystemMessage is stripped before storage."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        final_messages = [
            SystemMessage(content="sys\n\nproj"),
            HumanMessage(content="Hi"),
            AIMessage(content="Hello"),
        ]
        store_mock = MagicMock()
        await _collect(graph_events(final_messages), store_mock)

        store_mock.assert_called_once()
        stored = store_mock.call_args[0][1]
        assert len(stored) == 2
        assert [entry["type"] for entry in stored] == ["human", "ai"]
        assert all(entry["type"] != "system" for entry in stored)

    async def test_done_event_carries_messages_result_and_stats(self) -> None:
        """done carries the stored messages, the final text and tool stats."""
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        final_messages = [
            SystemMessage(content="sys"),
            HumanMessage(content="Hi"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search",
                        "args": {"q": "x"},
                        "id": "tc1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(content="tool output", tool_call_id="tc1"),
            AIMessage(content="final answer"),
        ]
        store_mock = MagicMock()
        result = await _collect(graph_events(final_messages), store_mock)

        done = [e for e in result if e["type"] == "done"][-1]
        stored = store_mock.call_args[0][1]
        assert done["messages"] == stored
        assert done["result"] == "final answer"
        stats = done["stats"]
        assert isinstance(stats, dict)
        assert stats["agent_steps"] == 1
        assert stats["total_tool_calls"] == 1
        assert stats["tool_trace"] == [
            {"name": "search", "args": {"q": "x"}, "result": "tool output"}
        ]
        # usage on stats mirrors the top-level accumulator, not a second source.
        assert stats["usage"] == done["usage"]

    async def test_cancel_persists_nothing(self) -> None:
        """A cancelled turn stores nothing but still emits done."""
        cancel = threading.Event()
        events = graph_events(
            [MagicMock()],
            inner=[_text_delta_event("first"), _text_delta_event("second", "r2")],
        )
        store_mock = MagicMock()

        with _patch_run_agent_stream(events, store_mock=store_mock):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            collected: list[dict[str, object]] = []
            async for evt in run_agent_stream(
                question="Hi",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path="/tmp/mcp.json",
                session_id="s1",
                cancel_event=cancel,
            ):
                collected.append(evt)
                if evt["type"] == "text_delta":
                    cancel.set()

        store_mock.assert_not_called()
        done_events = [e for e in collected if e["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["messages"] == []

    async def test_cancel_done_carries_partial_text(self) -> None:
        """The text streamed before the cancel survives on done['result']."""
        cancel = threading.Event()
        events = graph_events(
            [MagicMock()],
            inner=[_text_delta_event("partial"), _text_delta_event("dropped", "r2")],
        )
        store_mock = MagicMock()

        with _patch_run_agent_stream(events, store_mock=store_mock):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            collected: list[dict[str, object]] = []
            async for evt in run_agent_stream(
                question="Hi",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path="/tmp/mcp.json",
                session_id="s1",
                cancel_event=cancel,
            ):
                collected.append(evt)
                if evt["type"] == "text_delta":
                    cancel.set()

        done = [e for e in collected if e["type"] == "done"][-1]
        assert done["result"] == "partial"
        store_mock.assert_not_called()

    async def test_error_persists_nothing(self) -> None:
        """astream_events raising stores nothing; error event + re-raise stay."""
        # Hand-rolled patch set: _patch_run_agent_stream hard-wires
        # astream_events.return_value to an events list, so it cannot express
        # "raises". The agent must be a MagicMock() — an AsyncMock() child call
        # returns a coroutine, which `async for` rejects outright.
        mock_agent = MagicMock()
        mock_agent.astream_events.return_value = _RaisingAsyncIter(
            RuntimeError("agent error")
        )
        mock_client_cls = MagicMock()
        mock_client_cls.return_value.connections = {}
        store_mock = MagicMock()

        with (
            patch(f"{_AGENT_MOD_PATH}._load_mcp_server_config", return_value={}),
            patch(
                "langchain_mcp_adapters.client.MultiServerMCPClient", mock_client_cls
            ),
            patch("langgraph.prebuilt.create_react_agent", return_value=mock_agent),
            patch(f"{_STORAGE_MOD_PATH}.store_langchain_history", store_mock),
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

        store_mock.assert_not_called()
        error_events = [e for e in collected if e["type"] == "error"]
        assert len(error_events) == 1
        assert "agent error" in str(error_events[0]["message"])
        assert not [e for e in collected if e["type"] == "done"]

    async def test_no_terminal_event_done_carries_streamed_text(self) -> None:
        """Without a terminal graph event: no storage, but the text survives."""
        events = [_text_delta_event("streamed "), _text_delta_event("answer", "r2")]
        store_mock = MagicMock()
        result = await _collect(events, store_mock)

        store_mock.assert_not_called()
        done = [e for e in result if e["type"] == "done"][-1]
        assert done["result"] == "streamed answer"
        assert done["messages"] == []
        # Tool stats are derived from the final message list, so without one
        # they are omitted rather than reported as zeros — a zeroed trace would
        # claim "no tools ran" for a turn that may have called several.
        assert done["stats"] == {"usage": {}}

    async def test_no_terminal_event_omits_unresumable_session_id(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A turn that stored nothing under a new id does not report that id.

        Reporting it would wedge the caller: the next turn resumes the id, the
        resume guard finds no history file and raises, so icoder errors until
        ``/clear`` and a chained workflow turn aborts mid-run. Dropping the id
        makes the next turn start a fresh conversation instead.
        """
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        store_mock = MagicMock()

        result = await _collect([_text_delta_event("streamed answer")], store_mock)

        store_mock.assert_not_called()
        assert not list(tmp_path.rglob("*.json"))
        done = [e for e in result if e["type"] == "done"][-1]
        assert "session_id" not in done

        from mcp_coder.llm.providers.langchain import _resolve_session_id

        next_sid = _resolve_session_id(cast(Optional[str], done.get("session_id")))
        uuid.UUID(next_sid)

    async def test_no_terminal_event_keeps_session_id_of_stored_session(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A resumed session keeps its id even when the turn is not recorded.

        The prior history is still on disk, so the id stays resumable - only an
        id nothing was ever stored under is dropped.
        """
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        from mcp_coder.llm.storage.session_storage import store_langchain_history

        store_langchain_history("s1", [])
        store_mock = MagicMock()

        result = await _collect([_text_delta_event("streamed answer")], store_mock)

        store_mock.assert_not_called()
        done = [e for e in result if e["type"] == "done"][-1]
        assert done["session_id"] == "s1"


class TestAskAgentStreamBoundary:
    """``messages`` and ``stats`` are stripped at the provider boundary."""

    def test_ask_agent_stream_strips_messages_and_stats_from_done(self) -> None:
        """done loses messages+stats; session_id/usage/result and others survive."""

        async def _fake_run_agent_stream(
            **_kwargs: Any,
        ) -> AsyncIterator[dict[str, object]]:
            yield {"type": "text_delta", "text": "hello"}
            yield {
                "type": "done",
                "session_id": "s1",
                "usage": {"input_tokens": 7},
                "messages": [{"type": "human", "data": {"content": "Hi"}}],
                "result": "final answer",
                "stats": {
                    "agent_steps": 1,
                    "total_tool_calls": 1,
                    "tool_trace": [{"name": "search", "args": {}, "result": "r"}],
                    "usage": {"input_tokens": 7},
                },
            }

        config: dict[str, str | None] = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }

        with (
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
            patch(f"{_AGENT_MOD_PATH}._check_agent_dependencies"),
            patch(f"{_AGENT_MOD_PATH}.run_agent_stream", _fake_run_agent_stream),
        ):
            from mcp_coder.llm.providers.langchain import _ask_agent_stream

            result = list(
                _ask_agent_stream(
                    question="Hi",
                    config=config,
                    session_id="s1",
                    mcp_config=".mcp.json",
                    timeout=5,
                )
            )

        done = [e for e in result if e["type"] == "done"]
        assert len(done) == 1
        assert "messages" not in done[0]
        assert "stats" not in done[0]
        assert done[0]["session_id"] == "s1"
        assert done[0]["usage"] == {"input_tokens": 7}
        assert done[0]["result"] == "final answer"
        # Non-done events pass through untouched.
        assert [e for e in result if e["type"] == "text_delta"] == [
            {"type": "text_delta", "text": "hello"}
        ]
