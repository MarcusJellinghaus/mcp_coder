"""Tests for the shared LangChain message helpers in ``_messages.py``.

Message classes come from ``langchain_core.messages``; the directory conftest
substitutes lightweight real classes when langchain is not installed, so
``isinstance`` checks work either way.
"""

from typing import Any

from mcp_coder.llm.providers.langchain._messages import (
    assemble_messages,
    serialize_messages,
)


class _DictOnlyMessage:
    """Legacy-style message exposing ``.dict()`` but no ``.model_dump()``."""

    def __init__(self, msg_type: str, content: str) -> None:
        self._type = msg_type
        self._content = content

    def dict(self) -> dict[str, Any]:
        """Return the legacy pydantic-v1 style dump."""
        return {"type": self._type, "content": self._content}


class TestAssembleMessages:
    """Tests for assemble_messages()."""

    def test_assemble_orders_systems_history_then_question(self) -> None:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        system = SystemMessage(content="be helpful")
        history = [
            {"type": "human", "data": {"content": "prior question"}},
            {"type": "ai", "data": {"content": "prior answer"}},
        ]

        result = assemble_messages([system], history, "new question")

        assert len(result) == 4
        assert result[0] is system
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "prior question"
        assert isinstance(result[2], AIMessage)
        assert result[2].content == "prior answer"
        assert isinstance(result[3], HumanMessage)
        assert result[3].content == "new question"

    def test_assemble_without_systems(self) -> None:
        from langchain_core.messages import HumanMessage

        history = [{"type": "human", "data": {"content": "prior question"}}]

        result = assemble_messages(None, history, "new question")

        assert len(result) == 2
        assert result[0].content == "prior question"
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "new question"

    def test_assemble_with_empty_history(self) -> None:
        from langchain_core.messages import HumanMessage, SystemMessage

        system = SystemMessage(content="be helpful")

        result = assemble_messages([system], [], "new question")

        assert len(result) == 2
        assert result[0] is system
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "new question"

    def test_assemble_drops_system_messages_from_history(self) -> None:
        """Legacy history written by the pre-fix agent code may hold systems."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        system = SystemMessage(content="fresh system")
        history = [
            {"type": "system", "data": {"content": "stale system"}},
            {"type": "human", "data": {"content": "prior question"}},
            {"type": "ai", "data": {"content": "prior answer"}},
        ]

        result = assemble_messages([system], history, "new question")

        assert len(result) == 4
        assert result[0] is system
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "prior question"
        assert isinstance(result[2], AIMessage)
        assert result[2].content == "prior answer"
        assert isinstance(result[3], HumanMessage)
        assert result[3].content == "new question"
        assert not any(isinstance(m, SystemMessage) for m in result[1:])


class TestSerializeMessages:
    """Tests for serialize_messages()."""

    def test_serialize_strips_leading_system_messages(self) -> None:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="be helpful"),
            HumanMessage(content="question"),
            AIMessage(content="answer"),
        ]

        result = serialize_messages(messages)

        assert len(result) == 2
        assert [entry["type"] for entry in result] == ["human", "ai"]

    def test_serialize_keeps_non_leading_system_message(self) -> None:
        """Only *leading* systems are stripped — that is the documented contract."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages = [
            HumanMessage(content="question"),
            SystemMessage(content="mid-conversation system"),
            AIMessage(content="answer"),
        ]

        result = serialize_messages(messages)

        assert len(result) == 3
        assert [entry["type"] for entry in result] == ["human", "system", "ai"]

    def test_serialize_shape_round_trips(self) -> None:
        from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict

        messages = [HumanMessage(content="question"), AIMessage(content="answer")]

        result = serialize_messages(messages)

        for entry in result:
            assert set(entry) == {"type", "data"}
            assert isinstance(entry["data"], dict)
        rehydrated = messages_from_dict(result)
        assert len(rehydrated) == 2
        assert rehydrated[0].content == "question"
        assert rehydrated[1].content == "answer"

    def test_serialize_falls_back_to_dict_method(self) -> None:
        messages: list[Any] = [_DictOnlyMessage("human", "question")]

        result = serialize_messages(messages)

        assert result == [{"type": "human", "data": {"content": "question"}}]

    def test_serialize_empty_list(self) -> None:
        assert serialize_messages([]) == []
