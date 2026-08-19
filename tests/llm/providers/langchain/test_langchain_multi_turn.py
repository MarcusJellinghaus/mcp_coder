"""Multi-turn regression tests for the LangChain provider.

These drive the *streaming* text path (``ask_langchain_stream`` without
``mcp_config``) because that is the path ``mcp-coder prompt`` runs, and it is
where the ``--add-system-prompts`` multiple-system-message bug reproduces.

Message classes come from ``langchain_core.messages``; the directory conftest
substitutes lightweight real classes when langchain is not installed, so
``isinstance`` checks work either way.
"""

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
        "endpoint": None,
        "api_version": None,
    }


def _mock_chunk(content: str) -> MagicMock:
    """Create a mock AIMessageChunk with the given content."""
    chunk = MagicMock()
    chunk.content = content
    chunk.model_dump.return_value = {"type": "AIMessageChunk", "content": content}
    return chunk


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
