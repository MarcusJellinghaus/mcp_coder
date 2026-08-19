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

_MOD = "mcp_coder.llm.providers.langchain"


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
