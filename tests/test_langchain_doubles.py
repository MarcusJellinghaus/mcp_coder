from __future__ import annotations

import asyncio

import pytest

from tests.langchain_doubles import make_scripted_chat_model


def test_scripted_model_tool_call_then_done() -> None:
    pytest.importorskip("langchain_core")
    from langchain_core.messages import AIMessage

    def next_message(n: int) -> AIMessage:
        if n == 1:
            return AIMessage(
                content="", tool_calls=[{"name": "ping", "args": {}, "id": "call_1"}]
            )
        return AIMessage(content="done")

    model = make_scripted_chat_model(next_message, llm_type="test-scripted")

    assert model._llm_type == "test-scripted"
    assert model.bind_tools([]) is model
    with pytest.raises(NotImplementedError):
        model._generate(messages=[])

    first = asyncio.run(model._agenerate(messages=[]))
    assert first.generations[0].message.tool_calls[0]["name"] == "ping"

    second = asyncio.run(model._agenerate(messages=[]))
    assert second.generations[0].message.content == "done"
