"""Multi-turn regression tests for the LangChain provider.

These drive the *streaming* text path (``ask_langchain_stream`` without
``mcp_config``) because that is the path ``mcp-coder prompt`` runs, and it is
where the ``--add-system-prompts`` multiple-system-message bug reproduces.

Message classes come from ``langchain_core.messages``; the directory conftest
substitutes lightweight real classes when langchain is not installed, so
``isinstance`` checks work either way.
"""

import json
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from tests.llm.providers.langchain.conftest import async_events, graph_events

_MOD = "mcp_coder.llm.providers.langchain"
_AGENT_MOD = "mcp_coder.llm.providers.langchain.agent"
_STORAGE_MOD = "mcp_coder.llm.storage.session_storage"


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }


def _mock_chunk(content: str) -> MagicMock:
    """Create a mock AIMessageChunk with the given content."""
    chunk = MagicMock()
    chunk.content = content
    chunk.model_dump.return_value = {"type": "AIMessageChunk", "content": content}
    return chunk


def _reject_multiple_systems(messages: list[Any]) -> None:
    """Raise like a single-system provider does when handed >1 SystemMessage.

    Reproduces what LiteLLM's message transform does for Qwen-class backends:
    a conversation carrying more than one ``SystemMessage`` is refused outright.

    Args:
        messages: The outgoing message list handed to the model or the graph.

    Raises:
        ValueError: If *messages* contains more than one ``SystemMessage``.
    """
    from langchain_core.messages import SystemMessage

    if sum(isinstance(m, SystemMessage) for m in messages) > 1:
        raise ValueError("system messages must be at the beginning")


def _guarded_react_agent(seen: list[list[Any]]) -> MagicMock:
    """Build a stubbed react agent that rejects a second SystemMessage.

    Mock-class rule: this is a ``MagicMock()``, never an ``AsyncMock()`` —
    ``run_agent_stream`` does ``async for event in agent.astream_events(...)``,
    and an ``AsyncMock`` child call returns a coroutine, which ``async for``
    rejects before its return value is ever looked at.

    Args:
        seen: Collector appended with each turn's incoming message list.

    Returns:
        A ``MagicMock`` whose ``astream_events`` runs the guard on
        ``input["messages"]``, then yields a terminal graph event carrying the
        turn's final message list.
    """
    from langchain_core.messages import AIMessage

    def _astream_events(
        payload: dict[str, Any], **_kwargs: Any
    ) -> AsyncIterator[dict[str, object]]:
        sent = list(payload["messages"])
        _reject_multiple_systems(sent)
        seen.append(sent)
        # LangGraph's final state includes the SystemMessage it was handed;
        # stripping it on the way to storage is serialize_messages' job.
        final = sent + [AIMessage(content=f"answer {len(seen)}")]
        return async_events(graph_events(final))

    agent = MagicMock()
    agent.astream_events.side_effect = _astream_events
    return agent


class _FakeStore:
    """Dict-backed stand-in for load_/store_langchain_history."""

    def __init__(self) -> None:
        self.sessions: dict[str, list[dict[str, Any]]] = {}
        self.stored: list[list[dict[str, Any]]] = []

    def load(self, session_id: str) -> list[dict[str, Any]]:
        return list(self.sessions.get(session_id, []))

    def store(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        self.sessions[session_id] = list(messages)
        self.stored.append(list(messages))


class TestTextPathMultiTurn:
    """Two turns on one session must not accumulate system messages."""

    def test_two_turns_store_no_system_messages_and_send_one(self) -> None:
        """Stored history stays system-free; each call sends one leading system."""
        from langchain_core.messages import SystemMessage

        store = _FakeStore()
        mock_model = MagicMock()
        mock_model.stream.side_effect = [
            iter([_mock_chunk("answer one")]),
            iter([_mock_chunk("answer two")]),
        ]

        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", side_effect=store.load),
            patch(f"{_MOD}.store_langchain_history", side_effect=store.store),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            for question in ("first question", "second question"):
                list(
                    ask_langchain_stream(
                        question,
                        session_id="sess-1",
                        system_prompt="sys",
                        project_prompt="proj",
                    )
                )

        # Both turns persisted, and neither persisted a system message.
        assert len(store.stored) == 2
        for stored in store.stored:
            assert stored
            assert all(entry["type"] != "system" for entry in stored)
        assert [entry["type"] for entry in store.stored[0]] == ["human", "ai"]
        assert [entry["type"] for entry in store.stored[1]] == [
            "human",
            "ai",
            "human",
            "ai",
        ]

        # Every outgoing call carries exactly one SystemMessage, at index 0.
        assert len(mock_model.stream.call_args_list) == 2
        for call in mock_model.stream.call_args_list:
            sent = call[0][0]
            systems = [m for m in sent if isinstance(m, SystemMessage)]
            assert len(systems) == 1
            assert isinstance(sent[0], SystemMessage)
            assert sent[0].content == "sys\n\nproj"

        # Turn 2 really reloaded turn 1's exchange — so "no systems" is not vacuous.
        second_sent = mock_model.stream.call_args_list[1][0][0]
        assert [m.content for m in second_sent] == [
            "sys\n\nproj",
            "first question",
            "answer one",
            "second question",
        ]


class TestAgentPathMultiTurn:
    """Two agent turns on one session must not accumulate system messages."""

    async def test_two_turns_store_no_systems_and_send_one_system(self) -> None:
        """Turn 2 sends one leading system; neither turn stores a system."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        # The graph returns the *whole* conversation, systems included — that
        # is exactly what serialize_messages has to strip on the way out.
        turn_one_final: list[Any] = [
            SystemMessage(content="sys\n\nproj"),
            HumanMessage(content="first question"),
            AIMessage(content="answer one"),
        ]
        turn_two_final: list[Any] = turn_one_final + [
            HumanMessage(content="second question"),
            AIMessage(content="answer two"),
        ]

        # Mock-class rule: the react agent is a MagicMock(), never an
        # AsyncMock() — run_agent_stream does `async for` over the return
        # value of astream_events(), and an AsyncMock call returns a coroutine.
        mock_agent = MagicMock()
        mock_agent.astream_events.side_effect = [
            async_events(graph_events(turn_one_final)),
            async_events(graph_events(turn_two_final)),
        ]
        store_mock = MagicMock()

        with (
            patch(f"{_AGENT_MOD}._load_mcp_server_config", return_value={}),
            patch("langchain_mcp_adapters.client.MultiServerMCPClient", MagicMock()),
            patch("langgraph.prebuilt.create_react_agent", return_value=mock_agent),
            # run_agent_stream lazily imports store_langchain_history from the
            # storage module; without this patch the test writes into the
            # user's real ~/.mcp_coder/sessions/langchain/.
            patch(f"{_STORAGE_MOD}.store_langchain_history", store_mock),
        ):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            history: list[dict[str, Any]] = []
            for question in ("first question", "second question"):
                async for _ in run_agent_stream(
                    question=question,
                    chat_model=MagicMock(),
                    messages=history,
                    mcp_config_path="/tmp/mcp.json",
                    session_id="sess-agent",
                    system_messages=[SystemMessage(content="sys\n\nproj")],
                ):
                    pass
                history = list(store_mock.call_args[0][1])

        # Both turns persisted; no system entry in either stored history.
        assert store_mock.call_count == 2
        for call in store_mock.call_args_list:
            stored = call[0][1]
            assert stored
            assert all(entry["type"] != "system" for entry in stored)

        # Turn 2 sends exactly one SystemMessage, at index 0.
        second_sent = mock_agent.astream_events.call_args_list[1][0][0]["messages"]
        systems = [m for m in second_sent if isinstance(m, SystemMessage)]
        assert len(systems) == 1
        assert isinstance(second_sent[0], SystemMessage)

        # Turn 2 really reloaded turn 1's exchange — "no systems" is not vacuous.
        assert [m.content for m in second_sent] == [
            "sys\n\nproj",
            "first question",
            "answer one",
            "second question",
        ]


class TestSingleSystemProviderRejection:
    """A provider that refuses >1 SystemMessage must survive two turns.

    This is the original icoder symptom (issue #1116) from both directions:
    ``_build_system_messages`` emitted one ``SystemMessage`` per prompt, and the
    agent path then persisted the prepended systems so they accumulated every
    turn. Each test drives a real two-turn conversation with a system prompt
    *and* a project prompt through a stub that raises exactly like LiteLLM does
    for Qwen-class backends, so a regression on either turn fails loudly with
    ``system messages must be at the beginning`` rather than silently.
    """

    def test_text_path_two_turns_never_sends_two_systems(self) -> None:
        """``mcp-coder prompt --add-system-prompts``, twice on one session."""
        store = _FakeStore()
        mock_model = MagicMock()

        def _stream(messages: list[Any]) -> Iterator[Any]:
            _reject_multiple_systems(messages)
            return iter([_mock_chunk(f"answer {mock_model.stream.call_count}")])

        mock_model.stream.side_effect = _stream

        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", side_effect=store.load),
            patch(f"{_MOD}.store_langchain_history", side_effect=store.store),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            for question in ("first question", "second question"):
                # A guard hit surfaces here: _ask_text_stream re-raises after
                # yielding its error event.
                list(
                    ask_langchain_stream(
                        question,
                        session_id="reject-text",
                        system_prompt="sys",
                        project_prompt="proj",
                    )
                )

        assert mock_model.stream.call_count == 2
        assert len(store.stored) == 2
        for stored in store.stored:
            assert all(entry["type"] != "system" for entry in stored)

        # Turn 2 really carried turn 1's exchange, so "no systems" is not vacuous.
        second_sent = mock_model.stream.call_args_list[1][0][0]
        assert [m.content for m in second_sent] == [
            "sys\n\nproj",
            "first question",
            "answer 1",
            "second question",
        ]

    async def test_agent_path_two_turns_never_sends_two_systems(self) -> None:
        """``run_agent_stream`` twice, turn 2 fed turn 1's stored history."""
        from langchain_core.messages import SystemMessage

        seen: list[list[Any]] = []
        mock_agent = _guarded_react_agent(seen)
        store_mock = MagicMock()

        with (
            patch(f"{_AGENT_MOD}._load_mcp_server_config", return_value={}),
            patch("langchain_mcp_adapters.client.MultiServerMCPClient", MagicMock()),
            patch("langgraph.prebuilt.create_react_agent", return_value=mock_agent),
            # Keep storage out of the user's real ~/.mcp_coder/sessions/langchain/.
            patch(f"{_STORAGE_MOD}.store_langchain_history", store_mock),
        ):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            history: list[dict[str, Any]] = []
            for question in ("first question", "second question"):
                async for _ in run_agent_stream(
                    question=question,
                    chat_model=MagicMock(),
                    messages=history,
                    mcp_config_path="/tmp/mcp.json",
                    session_id="reject-agent",
                    system_messages=[SystemMessage(content="sys\n\nproj")],
                ):
                    pass
                history = list(store_mock.call_args[0][1])

        assert store_mock.call_count == 2
        for call in store_mock.call_args_list:
            assert all(entry["type"] != "system" for entry in call[0][1])

        assert len(seen) == 2
        assert [m.content for m in seen[1]] == [
            "sys\n\nproj",
            "first question",
            "answer 1",
            "second question",
        ]

    def test_icoder_agent_flow_two_turns_never_sends_two_systems(
        self, tmp_path: Path
    ) -> None:
        """The full icoder call chain, including a real session-file round trip.

        Unlike the unit-level agent test above, this drives
        ``ask_langchain_stream`` so the merge (``_build_system_messages``) and
        the ``_ask_agent_stream`` bridge are exercised, and it uses the real
        ``store_``/``load_langchain_history`` so turn 2's history comes back off
        disk through JSON and ``messages_from_dict`` — the flow icoder actually
        ran when the bug was reported.

        ``tools=[]`` is what makes ``run_agent_stream`` skip
        ``_load_mcp_server_config`` and ``MultiServerMCPClient``; ``mcp_config``
        still has to be truthy because that is what routes to the agent branch,
        but its value is never read.
        """
        from langchain_core.messages import SystemMessage

        seen: list[list[Any]] = []
        mock_agent = _guarded_react_agent(seen)
        session_file = tmp_path / "sessions" / "langchain" / "reject-icoder.json"
        on_disk: list[list[dict[str, Any]]] = []

        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_AGENT_MOD}._check_agent_dependencies"),
            patch("langgraph.prebuilt.create_react_agent", return_value=mock_agent),
            # Real storage functions, redirected under tmp_path.
            patch(f"{_STORAGE_MOD}.get_user_app_data_dir", return_value=tmp_path),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            for question in ("first question", "second question"):
                list(
                    ask_langchain_stream(
                        question,
                        session_id="reject-icoder",
                        mcp_config="ignored.json",
                        tools=[],
                        system_prompt="sys",
                        project_prompt="proj",
                    )
                )
                on_disk.append(json.loads(session_file.read_text(encoding="utf-8")))

        # The on-disk history is system-free after *both* turns.
        assert len(on_disk) == 2
        assert [entry["type"] for entry in on_disk[0]] == ["human", "ai"]
        assert [entry["type"] for entry in on_disk[1]] == [
            "human",
            "ai",
            "human",
            "ai",
        ]
        for stored in on_disk:
            assert all(entry["type"] != "system" for entry in stored)

        # Turn 2 sends exactly one SystemMessage, at index 0, carrying the merge.
        assert len(seen) == 2
        second_sent = seen[1]
        systems = [m for m in second_sent if isinstance(m, SystemMessage)]
        assert len(systems) == 1
        assert isinstance(second_sent[0], SystemMessage)
        assert second_sent[0].content == "sys\n\nproj"

        # ...and it really reloaded turn 1 off disk, so "no systems" is not vacuous.
        assert [m.content for m in second_sent] == [
            "sys\n\nproj",
            "first question",
            "answer 1",
            "second question",
        ]
